"""Generate and validate realistic sample request and response payloads in samples/."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = REPO_ROOT / "samples"


def generate_samples() -> None:
    """Generate canonical sample JSON payloads for documentation, testing, and API consumers."""
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    samples = {
        "plan_request.json": {
            "members": [
                {
                    "name": "Aarav",
                    "age_group": "child",
                    "sensitivity": "asthma_or_heart",
                    "routine": [
                        {"start_hour": 0, "end_hour": 7, "activity": "sleep", "mode": "home"},
                        {"start_hour": 7, "end_hour": 14, "activity": "light", "mode": "home"},
                        {"start_hour": 14, "end_hour": 16, "activity": "exercise", "mode": "outdoor"},
                        {"start_hour": 16, "end_hour": 24, "activity": "sleep", "mode": "home"},
                    ],
                },
                {
                    "name": "Priya",
                    "age_group": "adult",
                    "sensitivity": "none",
                    "routine": [
                        {"start_hour": 0, "end_hour": 8, "activity": "sleep", "mode": "home"},
                        {"start_hour": 8, "end_hour": 9, "activity": "commute", "mode": "metro"},
                        {"start_hour": 9, "end_hour": 18, "activity": "light", "mode": "home"},
                        {"start_hour": 18, "end_hour": 19, "activity": "commute", "mode": "metro"},
                        {"start_hour": 19, "end_hour": 24, "activity": "rest", "mode": "home"},
                    ],
                },
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
        },
        "plan_response.json": {
            "members_exposure": {
                "Aarav": {"total_dose_ug": 1184.22, "index": 61.6},
                "Priya": {"total_dose_ug": 1420.50, "index": 73.8},
            },
            "ventilation_window": {
                "start_hour": 13,
                "end_hour": 15,
                "mean_pm25": 77.5,
                "reason": "Optimal low-PM2.5 interval for natural ventilation",
            },
            "worst_window": {
                "start_hour": 19,
                "end_hour": 23,
                "mean_pm25": 285.0,
                "reason": "Peak nocturnal smog stagnation and inversion",
            },
            "inversion": {
                "hours": [22, 23, 0, 1, 2, 3, 4, 5, 6],
                "method": "boundary_layer_height",
            },
            "ranked_interventions": [
                {
                    "rank": 1,
                    "title": "Shift outdoor exercise to cleanest hour",
                    "cost_inr_per_month": 0.0,
                    "effort": 2,
                    "impact": 0.7,
                    "why_this_rank": "High cost-effectiveness zero-cost behavioral shift",
                    "provenance": {
                        "text": "Derived from diurnal exposure models",
                        "confidence": "high",
                    },
                }
            ],
            "ai_guidance": {
                "summary": "By shifting routines and sealing leaks, Aarav reduces inhaled dose by 38.4%.",
                "tips": [
                    "Open windows between 13:00 and 15:00 for ventilation.",
                    "Keep windows sealed during evening peak stagnation (19:00-23:00).",
                ],
                "answer": "Plan computed based on local meteorological parameters.",
            },
            "data_source": "sample",
            "provenance": {
                "text": "Diurnal microenvironment box model with verified meteorological inputs",
                "confidence": "high",
            },
        },
        "simulate_request.json": {
            "base_routine": [
                {"start_hour": 0, "end_hour": 8, "activity": "sleep", "mode": "home"},
                {"start_hour": 8, "end_hour": 17, "activity": "light", "mode": "home"},
                {"start_hour": 17, "end_hour": 19, "activity": "exercise", "mode": "outdoor"},
                {"start_hour": 19, "end_hour": 24, "activity": "sleep", "mode": "home"},
            ],
            "alt_routine": [
                {"start_hour": 0, "end_hour": 8, "activity": "sleep", "mode": "home"},
                {"start_hour": 8, "end_hour": 17, "activity": "light", "mode": "home"},
                {"start_hour": 17, "end_hour": 19, "activity": "rest", "mode": "home"},
                {"start_hour": 19, "end_hour": 24, "activity": "sleep", "mode": "home"},
            ],
            "home": {"leakiness": "average", "purifier": False},
            "age_group": "adult",
            "latitude": 28.61,
            "longitude": 77.21,
        },
        "simulate_response.json": {
            "index_before": 100.0,
            "index_after": 68.5,
            "dose_saved_ug": 145.2,
            "per_block_delta": [
                {
                    "start_hour": 17,
                    "end_hour": 19,
                    "base_dose_ug": 220.0,
                    "alt_dose_ug": 74.8,
                    "delta_ug": 145.2,
                }
            ],
            "provenance": {
                "text": "Comparative microenvironment diurnal integration",
                "confidence": "high",
            },
        },
        "home_analyze_request.json": {
            "cooking_fuel": "biomass",
            "kitchen_exhaust": "none",
            "incense": True,
            "mosquito_coil": True,
            "smokers": True,
            "sweeping": "dry",
        },
        "home_analyze_response.json": {
            "findings": [
                {
                    "source": "biomass_cooking",
                    "status": "suspected",
                    "confidence": "high",
                    "evidence": "Solid biomass fuel without chimney or mechanical exhaust",
                    "fixes": ["Switch to LPG/induction", "Cook near open window with cross-ventilation"],
                },
                {
                    "source": "incense_burning",
                    "status": "suspected",
                    "confidence": "medium",
                    "evidence": "Regular indoor burning of incense sticks or dhoop",
                    "fixes": ["Eliminate indoor burning", "Ventilate immediately after rituals"],
                },
            ]
        },
        "ask_request.json": {
            "question": "When is the safest time to open my windows today?",
            "facts": {
                "window_start": 13,
                "window_end": 15,
                "worst_start": 19,
                "worst_end": 23,
                "index_after": 68.5,
            },
            "language": "en",
        },
        "ask_response.json": {
            "summary": "Plan indicates cleanest ventilation window is 13:00 to 15:00.",
            "tips": [
                "Open windows between 13:00 and 15:00 when boundary layer heating disperses ground smog.",
                "Keep windows tightly shut during evening peak hours (19:00-23:00).",
            ],
            "answer": "The safest interval for natural ventilation today is from 13:00 to 15:00.",
            "is_red_flag": False,
            "red_flag": None,
        },
        "pledge_request.json": {
            "area_code": "DL-01",
            "action": "metro",
            "count": 2,
        },
        "pledge_response.json": {
            "status": "success",
            "message": "Pledge recorded successfully",
            "area_code": "DL-01",
        },
        "community_summary_response.json": {
            "participating_households": 24,
            "trips_avoided": 48,
            "co2_kg_avoided": 110.59,
            "pm25_note": "may reduce local traffic emissions; not a measured PM2.5 change",
        },
    }

    for filename, content in samples.items():
        file_path = SAMPLES_DIR / filename
        file_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
        print(f"Generated {file_path}")


if __name__ == "__main__":
    generate_samples()
