"""Contract Renewal · 90-Day Window — all six patterns composed.

The trace prints which pattern is firing at each step, mirroring the talk's
running example (slides 10–13).

Run: `python run.py`
"""
from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "patterns"))
from _common import log  # noqa: E402


# === P5 · the state machine (the spine) =====================================

ALLOWED = {
    "init":           {"window_open"},
    "window_open":    {"scoring"},
    "scoring":        {"offer_sent", "human_required"},
    "offer_sent":     {"closed", "human_required", "expired"},
    "human_required": {"offer_sent", "closed"},
    "closed":         set(),
    "expired":        set(),
}


@dataclass
class RenewalRow:
    id: str
    state: str = "init"
    version: int = 0
    data: dict[str, Any] = field(default_factory=dict)


STORE: dict[str, RenewalRow] = {}


def cas(row_id: str, expect_v: int, to: str, patch: dict[str, Any] | None = None) -> RenewalRow:
    row = STORE[row_id]
    if row.version != expect_v:
        raise RuntimeError(f"stale CAS: have v={row.version}, expected v={expect_v}")
    if to not in ALLOWED.get(row.state, set()):
        raise RuntimeError(f"illegal transition {row.state} → {to}")
    row.state = to
    row.version += 1
    if patch:
        row.data.update(patch)
    log("p5", f"cas → {to}", id=row_id, v=row.version)
    return row


# === P3 · event log =========================================================

EVENT_LOG: list[dict[str, Any]] = []


def emit(evt_type: str, **payload):
    e = {"id": str(uuid.uuid4())[:8], "type": evt_type, "payload": payload}
    EVENT_LOG.append(e)
    log("p3", "event appended", type=evt_type, id=e["id"])


# === P4 · gate ==============================================================

@dataclass
class Policy:
    max_discount_pct: int = 30
    version: str = "v7"


def gate(action: str, payload: dict[str, Any], policy: Policy) -> bool:
    if action == "publish_offer" and payload.get("discount_pct", 0) > policy.max_discount_pct:
        log("p4", "gate DENY", reason=f"discount {payload['discount_pct']}% > max {policy.max_discount_pct}%")
        return False
    log("p4", "gate allow", action=action)
    return True


# === P6 · HITL ==============================================================

SUSPENDED: list[dict[str, Any]] = []


def escalate(workflow_id: str, reason: str) -> None:
    SUSPENDED.append({"workflow_id": workflow_id, "reason": reason})
    log("p6", "escalation — workflow paused", workflow_id=workflow_id, reason=reason)


# === P1 + P2 · orchestrator with scatter-gather + saga ======================

def orchestrator_scatter_gather(renewal_id: str) -> dict[str, Any]:
    log("p1", "orchestrator dispatch", agents=["churn", "offer", "contract"])
    results = {}
    compensations = []

    # In real LangGraph this is a parallel fan-out; here we simulate sequentially
    # because the runnable code is meant to be read top-to-bottom.

    # Sub-agent: churn (pure read, no side-effect)
    results["churn"] = {"score": 0.72, "drivers": ["plan_eol", "support"]}
    log("p1", "sub:churn ok", score=0.72)

    # Sub-agent: offer (in-memory only — no side-effect at this stage)
    results["offer"] = {"plan": "premium_2yr", "discount_pct": 90}  # hallucinated discount
    log("p1", "sub:offer ok", discount=90)

    # Sub-agent: contract (writes to external CRM — needs a compensation)
    crm_record_id = f"crm-{renewal_id}-{len(EVENT_LOG)}"
    compensations.append(("crm.delete", crm_record_id))
    results["contract"] = {"term_months": 24, "crm_id": crm_record_id}
    log("p1", "sub:contract ok (wrote CRM)", crm_id=crm_record_id)

    # All succeeded → no rollback needed
    log("p2", "scatter-gather complete", results=len(results), saga=False)
    return results


# === The orchestration ======================================================

def run_renewal(renewal_id: str) -> None:
    log("trigger", "open window", renewal_id=renewal_id)
    STORE[renewal_id] = RenewalRow(id=renewal_id)
    policy = Policy()

    # Phase 1 · gate admits the trigger, state machine opens the window
    if not gate("open_window", {}, policy):
        return
    cas(renewal_id, 0, "window_open")

    # Phase 2 · P1+P2 fan out
    results = orchestrator_scatter_gather(renewal_id)
    cas(renewal_id, 1, "scoring", patch={"signals": results})

    # Phase 3 · mid-flight P3 event — PRODUCT_EOL on day -47
    emit("product_eol", customer="C1", plan="legacy_v1")
    log("p5", "absorbed mid-flight event into row data")
    STORE[renewal_id].data["product_eol"] = True

    # Phase 4 · scoring → offer_sent (or human_required if gate denies)
    offer = results["offer"]
    if gate("publish_offer", offer, policy):
        cas(renewal_id, 2, "offer_sent", patch={"offer": offer})
        log("end", "auto-shipped offer", id=renewal_id)
    else:
        cas(renewal_id, 2, "human_required", patch={"offer": offer, "reason": "discount_out_of_policy"})
        escalate(renewal_id, reason="discount_out_of_policy")
        log("end", "paused for human review", id=renewal_id)


def main():
    run_renewal("r-8f3a")
    log("audit", "final store", state=STORE["r-8f3a"].state, v=STORE["r-8f3a"].version)
    log("audit", "events", n=len(EVENT_LOG))
    log("audit", "suspended", n=len(SUSPENDED))


if __name__ == "__main__":
    main()
