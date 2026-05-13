"""P5 · Shared State Machine — durable row + CAS + timers

We model the renewal as a state machine with versioned transitions:

    pending → scoring → offer_sent → closed
                              ↓
                       human_required

Workers are PURE: they take (state, action) and return next_state. They never
hold state in memory. The store enforces CAS — if the row moved on, the worker
retries with the new version.

Run: `python langgraph_example.py`
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import log  # noqa: E402


# --- The state machine -------------------------------------------------------

ALLOWED_TRANSITIONS = {
    "pending":        {"scoring"},
    "scoring":        {"offer_sent", "human_required"},
    "offer_sent":     {"closed", "human_required", "expired"},
    "human_required": {"offer_sent", "closed", "expired"},
    "closed":         set(),
    "expired":        set(),
}


@dataclass
class Row:
    id: str
    state: str = "pending"
    version: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    pending_timer: tuple[str, int] | None = None  # (target_state, version_when_scheduled)


class StaleVersionError(Exception):
    pass


class IllegalTransitionError(Exception):
    pass


# --- The store: the source of truth -----------------------------------------

class Store:
    """In real life: Postgres `UPDATE ... WHERE version = $1` or DynamoDB CAS."""

    def __init__(self):
        self.rows: dict[str, Row] = {}

    def put_new(self, id: str) -> Row:
        row = Row(id=id)
        self.rows[id] = row
        return row

    def get(self, id: str) -> Row:
        return self.rows[id]

    def cas_transition(self, id: str, *, from_version: int, to_state: str,
                       data_patch: dict[str, Any] | None = None) -> Row:
        row = self.rows[id]
        if row.version != from_version:
            raise StaleVersionError(f"{id}: have v={row.version}, write expected v={from_version}")
        if to_state not in ALLOWED_TRANSITIONS.get(row.state, set()):
            raise IllegalTransitionError(f"{id}: {row.state} → {to_state} not allowed")
        row.state = to_state
        row.version += 1
        if data_patch:
            row.data.update(data_patch)
        log("store", "transition", id=id, state=row.state, v=row.version)
        return row

    def schedule_timer(self, id: str, *, target_state: str) -> None:
        row = self.rows[id]
        row.pending_timer = (target_state, row.version)
        log("store", "timer scheduled", id=id, target=target_state, at_v=row.version)

    def fire_timer_if_valid(self, id: str) -> None:
        """Timer is a no-op if the row has moved on since the timer was scheduled."""
        row = self.rows[id]
        if row.pending_timer is None:
            return
        target_state, sched_v = row.pending_timer
        if row.version != sched_v:
            log("store", "timer SKIPPED — row moved on", id=id, scheduled_at_v=sched_v, now_v=row.version)
            row.pending_timer = None
            return
        if target_state in ALLOWED_TRANSITIONS.get(row.state, set()):
            self.cas_transition(id, from_version=row.version, to_state=target_state)
        row.pending_timer = None


# --- Pure workers ------------------------------------------------------------

def worker_scorer(row: Row) -> tuple[int, str, dict[str, Any]]:
    """(state=pending) → scoring. Pure."""
    return row.version, "scoring", {"score": 0.72}


def worker_offer_writer(row: Row) -> tuple[int, str, dict[str, Any]]:
    """(state=scoring) → offer_sent OR human_required if discount over policy."""
    proposed_discount = 90  # hallucinated by the LLM
    if proposed_discount > 30:
        return row.version, "human_required", {"reason": "discount over policy"}
    return row.version, "offer_sent", {"discount_pct": proposed_discount}


def apply_worker(store: Store, id: str, worker) -> None:
    """Generic CAS apply with one retry on stale version."""
    for attempt in range(3):
        row = store.get(id)
        from_v, to_state, patch = worker(row)
        try:
            store.cas_transition(id, from_version=from_v, to_state=to_state, data_patch=patch)
            return
        except StaleVersionError as e:
            log("worker", "stale CAS, retrying", attempt=attempt, err=str(e))
        except IllegalTransitionError as e:
            log("worker", "illegal transition — aborting", err=str(e))
            return


def main():
    store = Store()
    store.put_new("r-001")

    apply_worker(store, "r-001", worker_scorer)
    apply_worker(store, "r-001", worker_offer_writer)

    # Schedule a 30-day expiry timer (we'll fire it immediately for the demo)
    store.schedule_timer("r-001", target_state="expired")

    # Now imagine a specialist manually closes the renewal — the timer should NOT fire.
    log("---", "specialist override happens")
    try:
        store.cas_transition("r-001", from_version=store.get("r-001").version,
                             to_state="offer_sent", data_patch={"override_by": "u.k.chen"})
    except IllegalTransitionError as e:
        log("override", "transition not allowed", err=str(e))

    store.fire_timer_if_valid("r-001")  # should skip — row moved on

    log("final", "row state", row=store.get("r-001"))


if __name__ == "__main__":
    main()
