"""Integration tests verifying full end-to-end user workflows in offline mode."""

from http import HTTPStatus

from starlette.testclient import TestClient

from app.engine.models import Activity, Mode
from app.services.community_service import clear_pledges


def test_full_offline_end_to_end_journey(client: TestClient) -> None:
    """Verify entire user journey works end-to-end without external network access.

    Journey:
    1. Operational health verification.
    2. Household plan creation with sample Delhi winter air data.
    3. Counterfactual routine simulation (comparing baseline vs shifted activity).
    4. Indoor source analysis from household survey.
    5. Conversational assistant Q&A with ground-truth facts.
    6. Collective community action pledge and aggregated impact reporting.
    """
    clear_pledges()

    # Step 1: Healthcheck
    health_res = client.get("/api/v1/health")
    assert health_res.status_code == HTTPStatus.OK
    assert health_res.json()["status"] == "ok"

    # Step 2: 24-hour Household Plan
    plan_payload = {
        "members": [
            {
                "name": "Aarav",
                "age_group": "child",
                "sensitivity": "asthma_or_heart",
                "routine": [
                    {
                        "start_hour": 0,
                        "end_hour": 7,
                        "activity": Activity.SLEEP.value,
                        "mode": Mode.HOME.value,
                    },
                    {
                        "start_hour": 7,
                        "end_hour": 8,
                        "activity": Activity.COOK.value,
                        "mode": Mode.HOME.value,
                    },
                    {
                        "start_hour": 8,
                        "end_hour": 14,
                        "activity": Activity.LIGHT.value,
                        "mode": Mode.HOME.value,
                    },
                    {
                        "start_hour": 14,
                        "end_hour": 16,
                        "activity": Activity.WALK.value,
                        "mode": Mode.WALK.value,
                    },
                    {
                        "start_hour": 16,
                        "end_hour": 24,
                        "activity": Activity.SLEEP.value,
                        "mode": Mode.HOME.value,
                    },
                ],
            }
        ],
        "home": {
            "leakiness": "average",
            "purifier": False,
            "windows_open_hours": [13, 14],
        },
        "latitude": 28.61,
        "longitude": 77.21,
        "budget_inr": 1000.0,
        "language": "en",
    }
    plan_res = client.post("/api/v1/plan", json=plan_payload)
    assert plan_res.status_code == HTTPStatus.OK
    plan_data = plan_res.json()
    assert "Aarav" in plan_data["members_exposure"]
    assert plan_data["data_source"] == "sample"
    assert len(plan_data["ranked_interventions"]) > 0

    # Step 3: Counterfactual Routine Simulation
    base_routine = [
        {"start_hour": 0, "end_hour": 8, "activity": "sleep", "mode": "home"},
        {"start_hour": 8, "end_hour": 17, "activity": "light", "mode": "home"},
        {"start_hour": 17, "end_hour": 19, "activity": "exercise", "mode": "outdoor"},
        {"start_hour": 19, "end_hour": 24, "activity": "sleep", "mode": "home"},
    ]
    # Shift outdoor exercise to indoor rest
    alt_routine = [
        {"start_hour": 0, "end_hour": 8, "activity": "sleep", "mode": "home"},
        {"start_hour": 8, "end_hour": 17, "activity": "light", "mode": "home"},
        {"start_hour": 17, "end_hour": 19, "activity": "rest", "mode": "home"},
        {"start_hour": 19, "end_hour": 24, "activity": "sleep", "mode": "home"},
    ]
    sim_payload = {
        "base_routine": base_routine,
        "alt_routine": alt_routine,
        "home": {"leakiness": "average", "purifier": False},
        "age_group": "child",
        "latitude": 28.61,
        "longitude": 77.21,
    }
    sim_res = client.post("/api/v1/simulate", json=sim_payload)
    assert sim_res.status_code == HTTPStatus.OK
    sim_data = sim_res.json()
    assert sim_data["index_before"] == 100.0
    assert sim_data["index_after"] < 100.0
    assert sim_data["dose_saved_ug"] > 0

    # Step 4: Indoor Source Analysis
    home_payload = {
        "cooking_fuel": "lpg",
        "kitchen_exhaust": "none",
        "incense": True,
        "mosquito_coil": True,
        "smokers": False,
        "sweeping": "dry",
    }
    home_res = client.post("/api/v1/home/analyze", json=home_payload)
    assert home_res.status_code == HTTPStatus.OK
    findings = home_res.json()["findings"]
    source_names = [f["source"] for f in findings]
    assert "incense_burning" in source_names
    assert "mosquito_coil" in source_names

    # Step 5: Guarded AI Assistant
    ask_payload = {
        "question": "What is our exposure score and how do we improve it?",
        "facts": {
            "index_after": sim_data["index_after"],
            "dose_saved": sim_data["dose_saved_ug"],
            "window_start": 13,
            "window_end": 15,
        },
        "language": "en",
    }
    ask_res = client.post("/api/v1/ask", json=ask_payload)
    assert ask_res.status_code == HTTPStatus.OK
    ask_data = ask_res.json()
    assert "summary" in ask_data
    assert "tips" in ask_data

    # Step 6: Community Action Pledge & Summary
    pledge_payload = {
        "area_code": "DL-05",
        "action": "metro",
        "count": 5,
    }
    pledge_res = client.post("/api/v1/community/pledges", json=pledge_payload)
    assert pledge_res.status_code == HTTPStatus.OK
    assert pledge_res.json()["status"] == "success"

    summary_res = client.get("/api/v1/community/summary?area_code=DL-05")
    assert summary_res.status_code == HTTPStatus.OK
    summary_data = summary_res.json()
    assert summary_data["participating_households"] == 1
    assert summary_data["trips_avoided"] == 5
    assert summary_data["co2_kg_avoided"] > 0
    assert "qualitative" in summary_data["pm25_note"].lower() or len(summary_data["pm25_note"]) > 0
