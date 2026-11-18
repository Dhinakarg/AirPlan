"""Household profile and emission source management service."""

from app.engine.indoor_sources import score_sources
from app.engine.models import HomeSurvey, SourceFinding


def analyze_home_sources(survey: HomeSurvey) -> list[SourceFinding]:
    """Diagnose indoor pollution sources from household survey responses.

    Args:
        survey: Household questionnaire response data.

    Returns:
        List of identified SourceFinding items ordered by likelihood.
    """
    return score_sources(survey)
