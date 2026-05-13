"""P6 · Human in the Loop — Google ADK

The four control planes:
  1. Kill switch       — cancellation_token revoked, agent halts in ~1s
  2. Escalation        — agent calls suspend(reason); workflow paused durably
  3. Approval          — sync wait under SLA; fallback policy on timeout
  4. Throttling        — N/min and $/day caps refuse over-budget work

This file is dual-mode: if `google-adk` is installed it wires the planes onto
ADK lifecycle callbacks; otherwise it runs a narrated walkthrough so the shape
is still legible.

Run: `python adk_example.py`
"""
from __future__ import annotations

import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import log  # noqa: E402


# ============================================================================
# Plane 1 · Kill switch
# ============================================================================

@dataclass
class CancellationToken:
    revoked: bool = False

    def revoke(self) -> None:
        self.revoked = True
        log("kill_switch", "REVOKED — agent will halt at next checkpoint")

    def check(self) -> None:
        if self.revoked:
            raise RuntimeError("CancellationToken revoked")


# ============================================================================
# Plane 2 · Escalation (durable suspend)
# ============================================================================

SUSPEND_QUEUE: deque[dict[str, Any]] = deque()


def suspend(workflow_id: str, reason: str) -> None:
    """In production: write a durable row, return a resume URL to a human queue."""
    SUSPEND_QUEUE.append({"workflow_id": workflow_id, "reason": reason, "at": time.time()})
    log("escalation", "suspended (durable)", workflow_id=workflow_id, reason=reason)


# ============================================================================
# Plane 3 · Approval (sync wait under SLA, fallback on timeout)
# ============================================================================

def request_approval(action: dict[str, Any], sla_seconds: float = 1.0) -> bool:
    """Block up to `sla_seconds`. In real life: post to Slack/PagerDuty/Sirena."""
    log("approval", "requested", action=action, sla_s=sla_seconds)
    # Simulate a fast no-response → fallback policy applies.
    time.sleep(min(sla_seconds, 0.2))
    log("approval", "SLA elapsed — falling back to deny (conservative)")
    return False


# ============================================================================
# Plane 4 · Throttling
# ============================================================================

@dataclass
class Throttle:
    per_min_cap: int = 60
    daily_dollars_cap: float = 100.0
    _calls_this_min: int = 0
    _spent_today: float = 0.0
    _minute_started: float = field(default_factory=time.monotonic)

    def admit(self, est_cost_usd: float) -> bool:
        now = time.monotonic()
        if now - self._minute_started > 60:
            self._minute_started = now
            self._calls_this_min = 0
        if self._calls_this_min >= self.per_min_cap:
            log("throttle", "DENY", reason="N/min cap")
            return False
        if self._spent_today + est_cost_usd > self.daily_dollars_cap:
            log("throttle", "DENY", reason="$/day cap", est=est_cost_usd, spent=self._spent_today)
            return False
        self._calls_this_min += 1
        self._spent_today += est_cost_usd
        return True


# ============================================================================
# The worker fleet
# ============================================================================

def worker_fleet(workflow_id: str, planes: dict[str, Any], *,
                 escalate_at: int | None = None,
                 approval_at: int | None = None,
                 max_steps: int = 5,
                 step_delay_s: float = 0.05) -> None:
    cancel: CancellationToken = planes["cancel"]
    throttle: Throttle = planes["throttle"]
    for step in range(max_steps):
        cancel.check()
        if not throttle.admit(est_cost_usd=10):
            log("worker", "throttled, skipping step", id=workflow_id, step=step)
            continue
        if escalate_at is not None and step == escalate_at:
            # Outside our envelope — escalate to a human
            suspend(workflow_id, reason="merger_of_two_contracts")
            return
        if approval_at is not None and step == approval_at:
            # Big side-effect — request approval
            if not request_approval({"action": "publish_offer", "discount_pct": 50}, sla_seconds=0.2):
                log("worker", "approval denied, halting", id=workflow_id, step=step)
                return
        log("worker", "did step", id=workflow_id, step=step)
        time.sleep(step_delay_s)


def _adk_available() -> bool:
    try:
        import google.adk  # noqa: F401
        return True
    except ImportError:
        return False


def main():
    log("init", "P6 four control planes")
    if _adk_available():
        log("adk", "google-adk detected — in production you'd wire these into "
                 "before_agent_callback / before_tool_callback hooks")

    # --- Plane 2 · Escalation: workflow A escalates at step 2 ----------------
    log("---", "scenario A · escalation")
    planes_a = {
        "cancel": CancellationToken(),
        "throttle": Throttle(per_min_cap=10, daily_dollars_cap=100),
    }
    worker_fleet("wf-A", planes_a, escalate_at=2)

    # --- Plane 3 · Approval: workflow B requests approval at step 1 ----------
    log("---", "scenario B · approval (SLA elapses → deny)")
    planes_b = {
        "cancel": CancellationToken(),
        "throttle": Throttle(per_min_cap=10, daily_dollars_cap=100),
    }
    worker_fleet("wf-B", planes_b, approval_at=1)

    # --- Plane 4 · Throttle: workflow C blows past the $/day cap -------------
    log("---", "scenario C · throttle ($/day cap)")
    planes_c = {
        "cancel": CancellationToken(),
        # cap is $25 and each step costs $10 → 3rd step is denied
        "throttle": Throttle(per_min_cap=10, daily_dollars_cap=25),
    }
    worker_fleet("wf-C", planes_c, max_steps=5)

    # --- Plane 1 · Kill switch: a long-running workflow gets revoked ---------
    log("---", "scenario D · kill switch")
    planes_d = {
        "cancel": CancellationToken(),
        "throttle": Throttle(per_min_cap=60, daily_dollars_cap=1000),
    }

    def kill_after_delay():
        # Fire well before the worker would naturally finish (20 steps * 0.1s = 2s)
        time.sleep(0.3)
        planes_d["cancel"].revoke()

    threading.Thread(target=kill_after_delay, daemon=True).start()

    try:
        worker_fleet("wf-D", planes_d, max_steps=20, step_delay_s=0.1)
    except RuntimeError as e:
        log("main", "halted by kill switch", err=str(e))

    log("audit", "suspend queue", entries=list(SUSPEND_QUEUE))


if __name__ == "__main__":
    main()
