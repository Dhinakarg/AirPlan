"""Community clean-air action and shared intervention service."""

import threading
from collections import deque
from typing import Any

from app.constants import MAX_PLEDGE_ENTRIES
from app.engine.community import aggregate_pledges
from app.engine.models import CommunityImpact, Pledge


class _PledgeStore:
    """Thread-safe bounded in-memory pledge storage container."""

    def __init__(self, capacity: int) -> None:
        self.lock = threading.Lock()
        self.pledges: deque[Pledge] = deque(maxlen=capacity)


_STORE = _PledgeStore(MAX_PLEDGE_ENTRIES)


def record_pledge(pledge: Pledge) -> dict[str, Any]:
    """Record a coarse privacy-preserving community clean-air action pledge.

    Args:
        pledge: Pledge object containing area_code, action, and count.

    Returns:
        Confirmation dictionary with recorded status.
    """
    with _STORE.lock:
        _STORE.pledges.append(pledge)
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
    with _STORE.lock:
        current_pledges = list(_STORE.pledges)

    if area_code:
        filtered = [p for p in current_pledges if p.area_code == area_code]
    else:
        filtered = current_pledges

    return aggregate_pledges(filtered)


def clear_pledges() -> None:
    """Clear all in-memory community pledges (useful for test isolation)."""
    with _STORE.lock:
        _STORE.pledges.clear()


def set_pledge_store_capacity(capacity: int) -> None:
    """Adjust in-memory pledge store capacity and re-bind deque with eviction.

    Args:
        capacity: Maximum entry bound for the pledge store.
    """
    with _STORE.lock:
        _STORE.pledges = deque(_STORE.pledges, maxlen=capacity)
