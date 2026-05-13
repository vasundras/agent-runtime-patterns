"""Convert IBM Telco rows into τ-bench-style task definitions.

A τ-bench task is, roughly:
  - an initial database state
  - a goal database state
  - a set of allowed tools
  - a policy document
  - one or more user "intents" the agent has to satisfy

We project each row of the Telco subset into one task with the row's churn /
contract / MRR shaping the goal state.

Run: `python evals/scenarios_telco.py`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from load_telco import load  # noqa: E402


POLICY_DOC = """Renewal policy v7 (effective 2026-01-01)

- Discount above 30% is NEVER auto-approved; route to human review.
- Contract mergers require human specialist + counsel.
- Two-year customers in good standing may be offered up to 30% off as renewal incentive.
- Month-to-month accounts with tenure >= 12 months may be offered annual contracts.
- Throttling: maximum 60 tool-calls per minute per renewal."""


ALLOWED_TOOLS = [
    "lookup_customer",
    "score_churn",
    "draft_offer",
    "publish_offer",
    "request_human_review",
    "accept_renewal",
    "expire_renewal",
]


def row_to_task(row: dict[str, str]) -> dict[str, Any]:
    """One τ-bench-style task per renewal."""
    initial = {
        "renewal_id": row["renewal_id"],
        "customer_id": row["customerID"],
        "state": row["current_state"],
        "version": 0,
        "monthly_charges": float(row["MonthlyCharges"]),
        "contract": row["Contract"],
        "tenure": int(row["tenure"]),
    }

    # Goal state derives from the Telco churn label + expected_path heuristic.
    if row["expected_path"] == "renewed":
        goal = {"state": "closed", "outcome": "renewed", "discount_pct_lte": 5}
    elif row["expected_path"] == "renewed_with_offer":
        goal = {"state": "closed", "outcome": "renewed", "discount_pct_lte": 30}
    elif row["expected_path"] == "restructured":
        goal = {"state": "closed", "outcome": "restructured"}
    elif row["expected_path"] == "churned":
        goal = {"state": "expired", "outcome": "churned"}
    elif row["expected_path"] == "escalated":
        goal = {"state": "human_required", "outcome": "escalated"}
    else:
        goal = {"state": "closed"}

    return {
        "task_id": row["renewal_id"],
        "domain": "telco_renewal",
        "initial_db": initial,
        "goal": goal,
        "allowed_tools": ALLOWED_TOOLS,
        "policy_doc": POLICY_DOC,
        "user_intent": _user_intent_for(row),
    }


def _user_intent_for(row: dict[str, str]) -> str:
    """Synthesize a user-side opening message based on the row."""
    if row["expected_path"] == "churned":
        return "I want to cancel my service."
    if row["expected_path"] == "restructured":
        return "My business changed. Can we restructure my plan?"
    if row["expected_path"] == "escalated":
        return "I'm merging this account with another contract."
    if row["expected_path"] == "renewed_with_offer":
        return "My contract is up for renewal — what offers do you have?"
    return "My contract is up for renewal."


def build_scenarios(subset: bool = True) -> list[dict[str, Any]]:
    return [row_to_task(r) for r in load(subset=subset)]


if __name__ == "__main__":
    scenarios = build_scenarios(subset=True)
    print(f"Built {len(scenarios)} τ-bench-style scenarios from Telco subset")
    print(f"Distribution by expected outcome:")
    from collections import Counter
    counts = Counter(s["goal"].get("outcome", "?") for s in scenarios)
    for k, v in counts.most_common():
        print(f"  {k:20s} {v:3d}")
    print()
    print("Sample scenario:")
    print(json.dumps(scenarios[0], indent=2))
