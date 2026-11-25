"""Unit tests for deterministic commute mode comparison and scenario differentiation."""

from http import HTTPStatus
from pathlib import Path
from typing import Any

from starlette.testclient import TestClient

from app.engine.commute import compare_commute_modes
from app.engine.enums import Mode


def test_compare_commute_modes_returns_all_six_modes() -> None:
    """Verify compare_commute_modes evaluates all six urban transit options."""
    cmp = compare_commute_modes(pm25_ug_m3=200.0, distance_km=10.0)
    assert len(cmp.options) == 6
    modes = [opt.mode for opt in cmp.options]
    assert modes == [
        Mode.WALK,
        Mode.CYCLE,
        Mode.METRO,
        Mode.BUS,
        Mode.AUTO_RICKSHAW,
        Mode.CAR,
    ]
    assert cmp.confidence == "low"
    assert "attenuation" in cmp.assumptions.lower()


def test_compare_commute_modes_respects_mode_factors_and_co2() -> None:
    """Verify relative exposure indices, zero-emission modes, and car CO2 ordering."""
    cmp = compare_commute_modes(pm25_ug_m3=180.0, distance_km=8.0)
    by_mode = {opt.mode: opt for opt in cmp.options}
    assert by_mode[Mode.CAR].exposure_index < by_mode[Mode.METRO].exposure_index
    assert by_mode[Mode.METRO].exposure_index < by_mode[Mode.WALK].exposure_index
    assert by_mode[Mode.WALK].exposure_index < by_mode[Mode.AUTO_RICKSHAW].exposure_index
    assert by_mode[Mode.WALK].co2_kg == 0.0
    assert by_mode[Mode.CYCLE].co2_kg == 0.0
    assert by_mode[Mode.METRO].co2_kg < by_mode[Mode.CAR].co2_kg
    assert by_mode[Mode.WALK].duration_minutes > by_mode[Mode.METRO].duration_minutes


def test_scenario_files_under_20kb() -> None:
    """Verify bundled demo scenario files exist and are under 20 KB each."""
    scenarios_dir = Path("app/data/scenarios")
    for name in ("severe.json", "moderate.json", "cleaner.json"):
        path = scenarios_dir / name
        assert path.exists()
        assert path.stat().st_size < 20_000


def _post_scenario(
    client: TestClient, valid_plan_payload: dict[str, Any], scenario: str
) -> dict[str, Any]:
    """Execute /api/v1/plan for a specific demo scenario."""
    res = client.post(
        "/api/v1/plan",
        json={**valid_plan_payload, "scenario": scenario, "budget_inr": 1500.0},
    )
    assert res.status_code == HTTPStatus.OK
    data: dict[str, Any] = res.json()
    return data


def test_plan_scenarios_produce_distinct_outputs(
    client: TestClient,
    valid_plan_payload: dict[str, Any],
) -> None:
    """Verify severe, moderate, and cleaner scenarios produce distinct plans and rankings."""
    sev = _post_scenario(client, valid_plan_payload, "severe")
    mod = _post_scenario(client, valid_plan_payload, "moderate")
    cln = _post_scenario(client, valid_plan_payload, "cleaner")

    assert sev["data_source"] == "demo:severe" and cln["data_source"] == "demo:cleaner"
    assert sev["ventilation_window"] is None
    assert mod["ventilation_window"] is not None and cln["ventilation_window"] is not None

    sev_dose = next(iter(sev["members_exposure"].values()))["total_dose_ug"]
    cln_dose = next(iter(cln["members_exposure"].values()))["total_dose_ug"]
    assert sev_dose > cln_dose

    sev_ranks = [r["intervention"]["id"] for r in sev["ranked_interventions"]]
    cln_ranks = [r["intervention"]["id"] for r in cln["ranked_interventions"]]
    assert sev_ranks != cln_ranks
    assert len(sev["commute_comparison"]["options"]) == 6
