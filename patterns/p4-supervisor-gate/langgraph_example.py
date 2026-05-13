"""P4 · Supervisor + Gate

Two halves:
  1. A *supervisor* runs N child workers and restarts any that miss heartbeat,
     with exponential backoff (Erlang/OTP one-for-one).
  2. A *gate* refuses out-of-policy side-effects and emits an audit record.

The two halves are independent — you can ship either without the other — but in
production you almost always want both.

Run: `python langgraph_example.py`
"""
from __future__ import annotations

import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import log  # noqa: E402


# ============================================================================
# Part 1 · Supervisor (one-for-one restart with exponential backoff)
# ============================================================================

@dataclass
class Child:
    name: str
    work: Callable[[], None]
    restarts: int = 0
    alive: bool = True
    last_heartbeat_ms: float = field(default_factory=lambda: time.monotonic() * 1000)


class Supervisor:
    def __init__(self, max_restarts: int = 3, backoff_base_s: float = 0.05):
        self.children: dict[str, Child] = {}
        self.max_restarts = max_restarts
        self.backoff_base_s = backoff_base_s

    def add(self, child: Child) -> None:
        self.children[child.name] = child

    def tick(self) -> None:
        """One supervisor cycle: run each child, restart any that died."""
        for child in self.children.values():
            if not child.alive:
                if child.restarts >= self.max_restarts:
                    log("supervisor", "giving up on child", name=child.name)
                    continue
                backoff = self.backoff_base_s * (2 ** child.restarts)
                log("supervisor", "restarting child", name=child.name, backoff_s=round(backoff, 3))
                time.sleep(backoff)
                child.restarts += 1
                child.alive = True
            try:
                child.work()
                child.last_heartbeat_ms = time.monotonic() * 1000
            except Exception as e:
                log("supervisor", "child died", name=child.name, err=str(e))
                child.alive = False


def make_flaky_worker(name: str, fail_after: int):
    state = {"n": 0}

    def work():
        state["n"] += 1
        if state["n"] == fail_after:
            raise RuntimeError(f"{name} crashed on iter {state['n']}")
        log(f"child:{name}", "tick", iter=state["n"])

    return work


# ============================================================================
# Part 2 · Gate (policy check before every side-effect)
# ============================================================================

@dataclass
class Policy:
    max_discount_pct: int = 30
    allow_auto_close: bool = True
    version: str = "v7"


@dataclass
class GateDecision:
    allow: bool
    reason: str
    policy_version: str


AUDIT_LOG: list[dict[str, Any]] = []


def gate(action: str, payload: dict[str, Any], policy: Policy) -> GateDecision:
    if action == "apply_discount":
        if payload.get("pct", 0) > policy.max_discount_pct:
            decision = GateDecision(False, f"discount {payload['pct']}% > max {policy.max_discount_pct}%", policy.version)
        else:
            decision = GateDecision(True, "within envelope", policy.version)
    elif action == "auto_close" and not policy.allow_auto_close:
        decision = GateDecision(False, "auto_close disabled by policy", policy.version)
    else:
        decision = GateDecision(True, "default allow", policy.version)

    AUDIT_LOG.append({"action": action, "payload": payload, "decision": decision.__dict__})
    log("gate", "decision", action=action, allow=decision.allow, reason=decision.reason)
    return decision


# ============================================================================
# Demo
# ============================================================================

def main():
    log("init", "P4 supervisor + gate demo")

    # Supervisor demo
    sup = Supervisor()
    sup.add(Child("crawler", make_flaky_worker("crawler", fail_after=2)))
    sup.add(Child("scorer", make_flaky_worker("scorer", fail_after=4)))
    for _ in range(6):
        sup.tick()

    # Gate demo
    log("---", "now the gate ---")
    policy = Policy()
    gate("apply_discount", {"pct": 15}, policy)   # allowed
    gate("apply_discount", {"pct": 90}, policy)   # denied — out-of-policy hallucination
    gate("auto_close", {"renewal_id": "r-1"}, policy)  # allowed

    log("audit", "trail length", n=len(AUDIT_LOG))
    for row in AUDIT_LOG:
        log("audit", row["action"], allow=row["decision"]["allow"], reason=row["decision"]["reason"])


if __name__ == "__main__":
    main()
