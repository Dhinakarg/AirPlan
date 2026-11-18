"""Community clean-air action and shared intervention service."""

import threading
from typing import Any

from app.engine.community import aggregate_pledges
from app.engine.models import CommunityImpact, Pledge

_LOCK = threading.Lock()
_PLEDGES: list[Pledge] = []


def record_pledge(pledge: Pledge) -> dict[str, Any]:
    """Record a coarse privacy-preserving community clean-air action pledge.

    Args:
        pledge: Pledge object containing area_code, action, and count.

    Returns:
        Confirmation dictionary with recorded status.
    """
    with _LOCK:
        _PLEDGES.append(pledge)
    return {
        "status": "success",
        "message": "Pledge recorded successfully",
        "area_code": pledge.area_code,
    }


def get_community_summary(area_code: str | None = None) -> CommunityImpact:
    """Aggregate community pledges and return collective emissions savings.

    Args:
        area_code: Optional coarse district code filter.

    Returns:
        CommunityImpact summary record.
    """
    with _LOCK:
        current_pledges = list(_PLEDGES)

    if area_code:
        filtered = [p for p in current_pledges if p.area_code == area_code]
    else:
        filtered = current_pledges

    return aggregate_pledges(filtered)


def clear_pledges() -> None:
    """Clear all in-memory community pledges (useful for test isolation)."""
    with _LOCK:
        _PLEDGES.clear()
