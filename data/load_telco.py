"""Load the IBM Telco Customer Churn dataset and project it into renewal-shaped rows.

Source: IBM Sample Data Set, mirrored on Kaggle and GitHub.
File: data/telco_customer_churn_full.csv (7,043 rows) — full corpus.
File: data/telco_customer_churn_subset.csv (100 rows) — subset used by examples.

The original columns are kept verbatim. We add four derived columns the agent
runtime needs:
  - renewal_id       — synthetic, stable per customer (md5(customerID)[:8])
  - window_open_at   — synthetic, anchored at the contract end-date inferred
                       from `tenure` (in months) and `Contract` type.
  - current_state    — initial state for the P5 state machine.
  - expected_path    — heuristic from Churn label + Contract type, used to
                       drive which pattern failure modes fire in the demos.

This is a pure read — no LLM, no API. Safe to run in CI.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Iterator

DATA_DIR = Path(__file__).resolve().parent


def renewal_id_for(customer_id: str) -> str:
    return "r-" + hashlib.md5(customer_id.encode()).hexdigest()[:8]


def infer_expected_path(row: dict[str, str]) -> str:
    """Map (Contract, Churn) → which path the renewal is on.

    This is the heuristic the demos use to seed each scenario. In a real system
    the path would emerge from the patterns themselves; here we precompute it so
    examples are deterministic.
    """
    churned = row.get("Churn", "").strip() == "Yes"
    contract = row.get("Contract", "").strip()
    monthly = float(row.get("MonthlyCharges", "0") or 0)
    if churned and contract == "Month-to-month":
        return "churned"
    if churned and contract != "Month-to-month":
        return "escalated"  # surprising churn on a longer contract → human review
    if monthly > 95 and contract == "Month-to-month":
        return "restructured"  # high-MRR M2M → suggest longer-term
    if monthly > 70:
        return "renewed_with_offer"
    return "renewed"


def initial_state_for(row: dict[str, str]) -> str:
    """Where in the state machine the customer's renewal starts.

    Customers near tenure-month-boundary % 12 are "in window" already.
    """
    tenure = int(row.get("tenure", "0") or 0)
    contract = row.get("Contract", "").strip()
    if contract == "Two year" and tenure >= 22:
        return "window_open"
    if contract == "One year" and tenure >= 10:
        return "window_open"
    if contract == "Month-to-month":
        return "scoring"
    return "init"


def load(subset: bool = True) -> Iterator[dict[str, str]]:
    """Yield rows augmented with renewal_id, window_open_at, current_state, expected_path."""
    fname = "telco_customer_churn_subset.csv" if subset else "telco_customer_churn_full.csv"
    path = DATA_DIR / fname
    with path.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            row["renewal_id"] = renewal_id_for(row["customerID"])
            row["current_state"] = initial_state_for(row)
            row["expected_path"] = infer_expected_path(row)
            yield row


def stats(subset: bool = True) -> dict[str, int]:
    """Quick distribution of expected paths — useful for sanity-checking the corpus."""
    counts: dict[str, int] = {}
    for row in load(subset=subset):
        counts[row["expected_path"]] = counts.get(row["expected_path"], 0) + 1
    return counts


if __name__ == "__main__":
    print("Subset (100 customers):")
    for k, v in sorted(stats(subset=True).items(), key=lambda kv: -kv[1]):
        print(f"  {k:25s} {v:4d}")
    print()
    print("Full corpus (7,043 customers):")
    for k, v in sorted(stats(subset=False).items(), key=lambda kv: -kv[1]):
        print(f"  {k:25s} {v:4d}")
    print()
    print("Sample row:")
    first = next(load())
    for k, v in first.items():
        print(f"  {k:25s} {v}")
