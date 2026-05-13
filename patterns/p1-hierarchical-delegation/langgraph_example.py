"""P1 · Hierarchical Delegation — LangGraph

Orchestrator dispatches a renewal task to three sub-agents (churn, offer, contract),
applies a partial-result policy on timeout, and merges.

Run: `python langgraph_example.py`
"""
from __future__ import annotations

import operator
import sys
from pathlib import Path
from typing import Annotated, Any, TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import get_llm, log  # noqa: E402

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # offline fallback so the file is still readable
    StateGraph = None  # type: ignore
    START = END = None  # type: ignore


# --- State (the typed I/O contract — talk slide 19) -------------------------

class RenewalState(TypedDict, total=False):
    renewal_id: str
    customer: dict[str, Any]
    # sub-agent outputs
    churn: dict[str, Any]
    offer: dict[str, Any]
    contract: dict[str, Any]
    # merged
    decision: dict[str, Any]
    # bookkeeping — Annotated reducer so multiple sub-agents can append failures
    # in parallel without clobbering each other.
    failures: Annotated[list[str], operator.add]


# --- Sub-agents (specialists) -----------------------------------------------

def sub_churn(state: RenewalState) -> RenewalState:
    log("sub:churn", "scoring churn", id=state["renewal_id"])
    # Real code: llm.invoke("classify churn risk for ...")
    return {"churn": {"score": 0.72, "drivers": ["plan_eol", "support_tickets"]}}


def sub_offer(state: RenewalState) -> RenewalState:
    log("sub:offer", "drafting offer", id=state["renewal_id"])
    # Simulate a slow/unreliable sub-agent so the partial-result policy fires.
    if state.get("customer", {}).get("force_offer_timeout"):
        log("sub:offer", "TIMEOUT (simulated)")
        return {"failures": ["offer:timeout"]}
    return {"offer": {"plan": "premium_2yr", "discount_pct": 15}}


def sub_contract(state: RenewalState) -> RenewalState:
    log("sub:contract", "building contract", id=state["renewal_id"])
    return {"contract": {"term_months": 24, "auto_renew": True}}


# --- Orchestrator: deterministic merge with partial-result policy -----------

def orchestrator_merge(state: RenewalState) -> RenewalState:
    """The orchestrator owns the merge. The LLM does not decide."""
    failures = state.get("failures", [])
    churn = state.get("churn")
    offer = state.get("offer")
    contract = state.get("contract")

    # Partial-result policy: if `offer` is missing, fall back to a safe default
    # rather than failing the whole renewal. This is the "merge · partial-result
    # policy" line in the talk's coordination slide.
    if not offer:
        log("orchestrator", "applying partial-result fallback", failures=failures)
        offer = {"plan": "renew_same", "discount_pct": 0, "fallback": True}

    decision = {
        "renewal_id": state["renewal_id"],
        "action": "renew" if churn and churn["score"] < 0.85 else "escalate",
        "offer": offer,
        "contract": contract,
        "partial": bool(failures),
    }
    log("orchestrator", "merged", decision=decision)
    return {"decision": decision}


# --- Graph -------------------------------------------------------------------

def build_graph():
    g = StateGraph(RenewalState)
    g.add_node("sub_churn", sub_churn)
    g.add_node("sub_offer", sub_offer)
    g.add_node("sub_contract", sub_contract)
    g.add_node("merge", orchestrator_merge)

    # Orchestrator dispatches to all three sub-agents in parallel
    g.add_edge(START, "sub_churn")
    g.add_edge(START, "sub_offer")
    g.add_edge(START, "sub_contract")
    # All three feed into merge
    g.add_edge("sub_churn", "merge")
    g.add_edge("sub_offer", "merge")
    g.add_edge("sub_contract", "merge")
    g.add_edge("merge", END)
    return g.compile()


def main():
    llm = get_llm()
    log("init", "starting hierarchical delegation", llm=llm.__class__.__name__)
    if StateGraph is None:
        log("init", "langgraph not installed — printing the graph shape only")
        log("graph", "START → [sub_churn | sub_offer | sub_contract] → merge → END")
        return

    app = build_graph()
    # Happy path
    out = app.invoke({"renewal_id": "r-8f3a", "customer": {"id": "C1"}})
    log("done", "happy path", action=out["decision"]["action"], partial=out["decision"]["partial"])

    # Forced timeout — partial-result policy fires
    out = app.invoke({"renewal_id": "r-9c11", "customer": {"id": "C2", "force_offer_timeout": True}})
    log("done", "with timeout", action=out["decision"]["action"], partial=out["decision"]["partial"])


if __name__ == "__main__":
    main()
