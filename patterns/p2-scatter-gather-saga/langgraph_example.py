"""P2 · Scatter-Gather + Saga — LangGraph

Three peers run in parallel against external systems. When one fails, the
coordinator walks the compensation log in reverse and undoes the side-effects
that the successful peers already wrote.

Run: `python langgraph_example.py`
"""
from __future__ import annotations

import operator
import sys
from pathlib import Path
from typing import Annotated, Any, TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import log  # noqa: E402

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    StateGraph = None  # type: ignore
    START = END = None  # type: ignore


# --- State -------------------------------------------------------------------

class SagaState(TypedDict, total=False):
    request_id: str
    # Annotated[list, operator.add] is LangGraph's way to express "merge by append"
    # — essential for the gather step so parallel peers don't clobber each other.
    results: Annotated[list[dict[str, Any]], operator.add]
    compensations: Annotated[list[dict[str, Any]], operator.add]
    failed_peer: str | None
    rolled_back: bool


# --- A tiny "external system" with side-effects ------------------------------

EXTERNAL_STATE: dict[str, Any] = {"billing": [], "crm": [], "email": []}


def write_external(system: str, payload: dict[str, Any]) -> dict[str, Any]:
    record = {"system": system, "id": f"{system}-{len(EXTERNAL_STATE[system]) + 1}", "payload": payload}
    EXTERNAL_STATE[system].append(record)
    return record


def undo_external(system: str, record_id: str) -> None:
    EXTERNAL_STATE[system] = [r for r in EXTERNAL_STATE[system] if r.get("id") != record_id]


# --- Peers (each emits a compensation entry alongside its result) ------------

def peer_a(state: SagaState) -> SagaState:
    log("peer:A", "ok")
    rec = write_external("crm", {"req": state["request_id"], "note": "renewal opened"})
    return {
        "results": [{"peer": "A", "ok": True, "record": rec}],
        "compensations": [{"peer": "A", "undo": ("crm", rec["id"])}],
    }


def peer_b(state: SagaState) -> SagaState:
    # Simulated timeout / failure
    log("peer:B", "TIMEOUT (simulated)")
    return {"results": [{"peer": "B", "ok": False, "error": "timeout"}], "failed_peer": "B"}


def peer_c(state: SagaState) -> SagaState:
    log("peer:C", "ok, wrote external billing")
    rec = write_external("billing", {"req": state["request_id"], "amount": 1200})
    return {
        "results": [{"peer": "C", "ok": True, "record": rec}],
        "compensations": [{"peer": "C", "undo": ("billing", rec["id"])}],
    }


# --- Aggregator with saga ----------------------------------------------------

def aggregate_or_compensate(state: SagaState) -> SagaState:
    if state.get("failed_peer"):
        log("saga", "failure detected, rolling back", failed=state["failed_peer"])
        # Walk compensations in REVERSE order — sagas, Garcia-Molina & Salem 1987
        for entry in reversed(state.get("compensations", [])):
            system, record_id = entry["undo"]
            log("saga", "compensate", peer=entry["peer"], system=system, id=record_id)
            undo_external(system, record_id)
        return {"rolled_back": True}
    log("aggregate", "all peers ok", results=len(state.get("results", [])))
    return {"rolled_back": False}


def build_graph():
    g = StateGraph(SagaState)
    g.add_node("peer_a", peer_a)
    g.add_node("peer_b", peer_b)
    g.add_node("peer_c", peer_c)
    g.add_node("aggregate", aggregate_or_compensate)
    g.add_edge(START, "peer_a")
    g.add_edge(START, "peer_b")
    g.add_edge(START, "peer_c")
    g.add_edge("peer_a", "aggregate")
    g.add_edge("peer_b", "aggregate")
    g.add_edge("peer_c", "aggregate")
    g.add_edge("aggregate", END)
    return g.compile()


def main():
    if StateGraph is None:
        log("init", "langgraph not installed — printing the graph shape only")
        log("graph", "START → [peer_a | peer_b(fails) | peer_c] → aggregate(saga rollback) → END")
        return

    app = build_graph()
    out = app.invoke({"request_id": "req-123"})
    log("final", "external state after run", state=EXTERNAL_STATE, rolled_back=out["rolled_back"])
    # After rollback, crm and billing should be empty again.
    assert EXTERNAL_STATE["crm"] == [] and EXTERNAL_STATE["billing"] == [], "saga did not clean up"
    log("final", "saga compensation verified ✓")


if __name__ == "__main__":
    main()
