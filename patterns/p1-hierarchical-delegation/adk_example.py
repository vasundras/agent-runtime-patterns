"""P1 · Hierarchical Delegation — Google ADK variant

ADK's `ParallelAgent` + `SequentialAgent` express the orchestrator/worker shape
natively: a parent agent that fans out to sub-agents and then sequences a merge
step. This file shows the same renewal-routing problem in ADK terms.

Run: `python adk_example.py`  (works without ADK installed — falls back to a
narrated walk-through so the structure is still legible.)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import log  # noqa: E402


def _adk_available() -> bool:
    try:
        import google.adk  # noqa: F401
        return True
    except ImportError:
        return False


def main():
    if not _adk_available():
        log("init", "google-adk not installed — printing ADK composition only")
        log("adk", "ParallelAgent(sub_churn, sub_offer, sub_contract)")
        log("adk", "  → SequentialAgent → MergeAgent (deterministic merge)")
        log("adk", "  → Output: RenewalDecision")
        log("note", "Install google-adk and re-run for a live execution.")
        return

    # Live ADK path (only runs when the SDK is installed)
    from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

    sub_churn = LlmAgent(
        name="sub_churn",
        instruction="Score churn risk for the customer. Return JSON.",
        output_key="churn",
    )
    sub_offer = LlmAgent(
        name="sub_offer",
        instruction="Draft a renewal offer. Return JSON.",
        output_key="offer",
    )
    sub_contract = LlmAgent(
        name="sub_contract",
        instruction="Build a contract draft. Return JSON.",
        output_key="contract",
    )

    fan_out = ParallelAgent(
        name="fan_out",
        sub_agents=[sub_churn, sub_offer, sub_contract],
    )

    merge = LlmAgent(
        name="merge",
        # The merge is *the* place where deterministic policy lives.
        # ADK lets us bind tool calls or output schemas here — we do NOT let
        # the merge LLM redo the sub-agents' work.
        instruction=(
            "Given churn, offer, contract in state, apply the partial-result "
            "policy and return a final RenewalDecision JSON."
        ),
        output_key="decision",
    )

    orchestrator = SequentialAgent(name="orchestrator", sub_agents=[fan_out, merge])

    # Pseudo: in real ADK you'd run via runner.run_async()
    log("adk", "orchestrator wired", root=orchestrator.name)


if __name__ == "__main__":
    main()
