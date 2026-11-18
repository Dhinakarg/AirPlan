"""API endpoint route definitions."""

from typing import Any

from fastapi import APIRouter, Query

from app.api.schemas import (
    AskRequest,
    AskResponse,
    FamilyMemberInput,
    HomeAnalyzeRequest,
    HomeAnalyzeResponse,
    PlanRequest,
    PlanResponse,
    PledgeRequest,
    PledgeResponse,
    SimulateRequest,
)
from app.engine.models import (
    CommunityImpact,
    HomeSurvey,
    Pledge,
    RoutineComparison,
)
from app.services.assistant_service import ask_assistant
from app.services.community_service import get_community_summary, record_pledge
from app.services.home_service import analyze_home_sources
from app.services.plan_service import MemberPlanInput, create_clean_air_plan
from app.services.simulate_service import run_simulation

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict[str, str]:
    """Operational health check endpoint for api/v1."""
    return {"status": "ok"}


def _to_member_inputs(members: list[FamilyMemberInput]) -> list[MemberPlanInput]:
    """Convert API member request payloads to service domain inputs."""
    return [
        MemberPlanInput(
            name=m.name,
            age_group=m.age_group,
            sensitivity=m.sensitivity,
            routine=m.routine,
        )
        for m in members
    ]


@router.post("/plan", response_model=PlanResponse)
def plan_endpoint(req: PlanRequest) -> dict[str, Any]:
    """Build personalized 24-hour clean-air exposure plan and recommendations."""
    return create_clean_air_plan(
        members=_to_member_inputs(req.members),
        home=req.home,
        latitude=req.latitude,
        longitude=req.longitude,
        date=req.date,
        budget_inr=req.budget_inr,
        context=req.context,
        language=req.language,
    )


@router.post("/simulate", response_model=RoutineComparison)
def simulate_endpoint(req: SimulateRequest) -> RoutineComparison:
    """Simulate routine changes and evaluate particulate dose reductions."""
    return run_simulation(
        base_routine=req.base_routine,
        alt_routine=req.alt_routine,
        home=req.home,
        age_group=req.age_group,
        latitude=req.latitude,
        longitude=req.longitude,
        date=req.date,
    )


@router.post("/home/analyze", response_model=HomeAnalyzeResponse)
def home_analyze_endpoint(req: HomeAnalyzeRequest) -> HomeAnalyzeResponse:
    """Diagnose indoor emission sources and suggest household mitigation fixes."""
    survey = HomeSurvey(
        cooking_fuel=req.cooking_fuel,
        kitchen_exhaust=req.kitchen_exhaust,
        incense=req.incense,
        mosquito_coil=req.mosquito_coil,
        smokers=req.smokers,
        pets=req.pets,
        sweeping=req.sweeping,
        indoor_pm25_reading=req.indoor_pm25_reading,
    )
    findings = analyze_home_sources(survey)
    return HomeAnalyzeResponse(findings=findings)


@router.post("/community/pledges", response_model=PledgeResponse)
def community_pledge_endpoint(req: PledgeRequest) -> dict[str, Any]:
    """Register privacy-preserving community clean-air action pledge."""
    pledge = Pledge(area_code=req.area_code, action=req.action, count=req.count)
    return record_pledge(pledge)


@router.get("/community/summary", response_model=CommunityImpact)
def community_summary_endpoint(
    area_code: str | None = Query(default=None, pattern=r"^[A-Z0-9-]{3,10}$"),
) -> CommunityImpact:
    """Retrieve aggregated community emissions savings and trips avoided."""
    return get_community_summary(area_code)


@router.post("/ask", response_model=AskResponse)
def ask_endpoint(req: AskRequest) -> dict[str, Any]:
    """Answer clean-air inquiries with red-flag triage, injection screening, and AI."""
    return ask_assistant(question=req.question, facts=req.facts, lang=req.language)
