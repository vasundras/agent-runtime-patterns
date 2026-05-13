"""P6 · Human in the Loop — LangGraph variant

Uses LangGraph's `interrupt_before` to pause the graph at human checkpoints.
The checkpointer makes the suspend durable.

Run: `python langgraph_example.py`
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import log  # noqa: E402

try:
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph
except ImportError:
    StateGraph = None  # type: ignore
    MemorySaver = None  # type: ignore
    START = END = None  # type: ignore


class HitlState(TypedDict, total=False):
    workflow_id: str
    proposed_action: dict
    human_decision: str  # "approve" | "deny" | None
    halted: bool


def propose(state: HitlState) -> HitlState:
    log("propose", "agent drafts action", id=state["workflow_id"])
    return {"proposed_action": {"discount_pct": 50, "publish": True}}


def execute(state: HitlState) -> HitlState:
    if state.get("human_decision") != "approve":
        log("execute", "halted — no human approval")
        return {"halted": True}
    log("execute", "publishing", action=state["proposed_action"])
    return {"halted": False}


def main():
    if StateGraph is None:
        log("init", "langgraph not installed — printing structure only")
        log("graph", "START → propose → [INTERRUPT: human approves] → execute → END")
        return

    g = StateGraph(HitlState)
    g.add_node("propose", propose)
    g.add_node("execute", execute)
    g.add_edge(START, "propose")
    g.add_edge("propose", "execute")
    g.add_edge("execute", END)

    saver = MemorySaver()
    # interrupt_before='execute' makes the graph pause durably at that node
    # until we call .invoke(..., command=Command(resume=...))
    app = g.compile(checkpointer=saver, interrupt_before=["execute"])

    cfg = {"configurable": {"thread_id": "wf-42"}}
    out = app.invoke({"workflow_id": "wf-42"}, cfg)
    log("paused", "state after interrupt", out=out)

    # A human reviews and resumes with approve=False (deny the 50% discount)
    log("human", "denies the action")
    app.update_state(cfg, {"human_decision": "deny"})
    out = app.invoke(None, cfg)  # resume
    log("done", "halted" if out.get("halted") else "shipped")


if __name__ == "__main__":
    main()
