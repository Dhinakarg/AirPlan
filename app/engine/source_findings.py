"""Source finding builders for indoor combustion and infiltration diagnostics."""

from typing import Literal

from app.constants import LIKELIHOOD_AMBIENT_INFILTRATION
from app.engine.models import SourceFinding

SourceStatus = Literal["suspected", "measured"]


def biomass_finding(fuel: str, exh: str, like: float, status: SourceStatus) -> SourceFinding:
    """Create finding for solid biomass / wood combustion."""
    return SourceFinding(
        source="biomass_cooking",
        likelihood=like,
        evidence=f"Combustion of {fuel} with {exh} exhaust",
        status=status,
        fixes=[
            "Switch to induction or LPG cooktop",
            "Install exterior-vented exhaust chimney",
            "Isolate kitchen enclosure from living rooms",
        ],
    )


def lpg_finding(fuel: str, exh: str, like: float, status: SourceStatus) -> SourceFinding:
    """Create finding for unvented or poorly vented gas cooking."""
    return SourceFinding(
        source="unvented_lpg_cooking",
        likelihood=like,
        evidence=f"Cooking with {fuel} and {exh} exhaust",
        status=status,
        fixes=[
            "Install ducted exterior kitchen exhaust",
            "Maintain continuous natural draft during stove operation",
        ],
    )


def ambient_infiltration_finding(reading: float) -> SourceFinding:
    """Build fallback finding when high reading exists with no identified domestic sources."""
    return SourceFinding(
        source="ambient_infiltration",
        likelihood=LIKELIHOOD_AMBIENT_INFILTRATION,
        evidence=f"Indoor PM2.5 ({reading} ug/m3) exceeds threshold",
        status="measured",
        fixes=[
            "Seal leaky door thresholds and window gaps",
            "Deploy HEPA room air purifier",
        ],
    )
