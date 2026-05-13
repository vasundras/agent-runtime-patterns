"""P3 · Event-Driven Sequencing — LangGraph + append-only log

We model the log as a list of immutable events (id, type, payload,
model_version, idempotency_key). Three consumers process the log:
- churn_watcher reacts to usage_drop and emits churn_score
- migration_agent reacts to plan_eol
- closer reacts to accepted

Each consumer's side-effects are gated by an idempotency key so re-play is safe.

Run: `python langgraph_example.py`
"""
from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import log  # noqa: E402


@dataclass(frozen=True)
class Event:
    id: str
    type: str
    payload: dict[str, Any]
    model_version: str = "claude-4.5"
    idempotency_key: str = ""


@dataclass
class EventLog:
    """Append-only log. In production: Kafka, EventStoreDB, Postgres + LSN."""
    events: list[Event] = field(default_factory=list)

    def append(self, evt: Event) -> None:
        log("log", "append", id=evt.id, type=evt.type)
        self.events.append(evt)

    def replay_from(self, start: int = 0):
        return iter(self.events[start:])


# Idempotency store — a real one is Redis with TTL or Postgres unique index.
PROCESSED_KEYS: set[str] = set()


def with_idempotency(consumer):
    """Decorator: each consumer call must declare an idempotency key. If we've
    already processed that key, we skip the side-effect — replay-safe."""

    def wrapped(evt: Event, log_obj: EventLog):
        key = evt.idempotency_key or f"{consumer.__name__}:{evt.id}"
        if key in PROCESSED_KEYS:
            log("idem", "skip (already processed)", consumer=consumer.__name__, key=key)
            return
        consumer(evt, log_obj)
        PROCESSED_KEYS.add(key)

    return wrapped


# --- Consumers ---------------------------------------------------------------

@with_idempotency
def churn_watcher(evt: Event, log_obj: EventLog) -> None:
    if evt.type != "usage_drop":
        return
    log("churn_watcher", "scoring", customer=evt.payload["customer"])
    log_obj.append(Event(id=str(uuid.uuid4()), type="churn_score",
                         payload={"customer": evt.payload["customer"], "score": 0.81}))


@with_idempotency
def migration_agent(evt: Event, log_obj: EventLog) -> None:
    if evt.type != "plan_eol":
        return
    log("migration_agent", "proposing migration", from_=evt.payload["plan"])
    log_obj.append(Event(id=str(uuid.uuid4()), type="migration_offer",
                         payload={"customer": evt.payload["customer"], "to_plan": "premium_v2"}))


@with_idempotency
def closer(evt: Event, log_obj: EventLog) -> None:
    if evt.type != "accepted":
        return
    log("closer", "closing renewal", customer=evt.payload["customer"])
    log_obj.append(Event(id=str(uuid.uuid4()), type="renewal_closed",
                         payload={"customer": evt.payload["customer"]}))


# --- Dispatcher --------------------------------------------------------------

def dispatch(log_obj: EventLog) -> None:
    """Tail the log; route each event to all consumers (at-least-once)."""
    cursor = 0
    consumers = [churn_watcher, migration_agent, closer]
    # We iterate until the log is stable.
    while True:
        new_events = list(log_obj.replay_from(cursor))
        if not new_events:
            return
        for evt in new_events:
            for c in consumers:
                c(evt, log_obj)
        cursor += len(new_events)


def main():
    elog = EventLog()
    # Seed the log with three real-world events
    elog.append(Event(id="e1", type="usage_drop",
                      payload={"customer": "C1", "delta_pct": -30}))
    elog.append(Event(id="e2", type="plan_eol",
                      payload={"customer": "C1", "plan": "legacy_v1"}))
    elog.append(Event(id="e3", type="accepted",
                      payload={"customer": "C1", "offer": "premium_v2"}))

    dispatch(elog)

    log("snapshot", "final log size", n=len(elog.events))
    for e in elog.events:
        log("event", e.type, id=e.id, payload=e.payload)

    # Replay the entire log — idempotency should suppress duplicate work.
    log("replay", "rewinding to event 0")
    dispatch(elog)
    log("done", "no duplicates emitted ✓" if len(elog.events) == 6 else "DUPLICATES!")


if __name__ == "__main__":
    main()
