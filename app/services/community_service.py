"""Community clean-air action and shared intervention service."""

import threading
from collections import deque
from typing import Any

from app.constants import MAX_PLEDGE_ENTRIES
from app.engine.community import aggregate_pledges
from app.engine.models import CommunityImpact, Pledge


class PledgeStore:
    """Thread-safe bounded in-memory pledge storage container."""

    def __init__(self, capacity: int = MAX_PLEDGE_ENTRIES) -> None:
        """Initialize PledgeStore with capacity limit."""
        self.lock = threading.Lock()
        self.pledges: deque[Pledge] = deque(maxlen=capacity)

    def record(self, pledge: Pledge) -> dict[str, Any]:
        """Insert pledge with thread-safe eviction if capacity is reached."""
        with self.lock:
            self.pledges.append(pledge)
        return {
            "status": "success",
            "message": "Pledge recorded successfully",
            "area_code": pledge.area_code,
        }

    def summary(self, area_code: str | None = None) -> CommunityImpact:
        """Aggregate recorded pledges filtered optionally by area code."""
        with self.lock:
            current_pledges = list(self.pledges)
        if area_code:
            filtered = [p for p in current_pledges if p.area_code == area_code]
        else:
            filtered = current_pledges
        return aggregate_pledges(filtered)

    def clear(self) -> None:
        """Purge all stored pledges."""
        with self.lock:
            self.pledges.clear()

    def set_capacity(self, capacity: int) -> None:
        """Adjust maximum storage capacity with eviction."""
        with self.lock:
            self.pledges = deque(self.pledges, maxlen=capacity)


_STORE = PledgeStore(MAX_PLEDGE_ENTRIES)


def record_pledge(pledge: Pledge, store: PledgeStore | None = None) -> dict[str, Any]:
    """Record a coarse privacy-preserving community clean-air action pledge."""
    return (store or _STORE).record(pledge)


def get_community_summary(
    area_code: str | None = None,
    store: PledgeStore | None = None,
) -> CommunityImpact:
    """Aggregate community pledges and return collective emissions savings."""
    return (store or _STORE).summary(area_code)


def clear_pledges(store: PledgeStore | None = None) -> None:
    """Clear all in-memory community pledges (useful for test isolation)."""
    (store or _STORE).clear()


def set_pledge_store_capacity(capacity: int, store: PledgeStore | None = None) -> None:
    """Adjust in-memory pledge store capacity and re-bind deque with eviction."""
    (store or _STORE).set_capacity(capacity)
