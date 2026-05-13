# Data

Real public data plus a few hand-crafted scenarios.

| File | Origin | Used by |
|---|---|---|
| `telco_customer_churn_full.csv` | **IBM Telco Customer Churn**, 7,043 real customer records (CC0-equivalent). | P1, P2, contract-renewal at scale. |
| `telco_customer_churn_subset.csv` | First 100 rows of the IBM dataset — fixed sample for deterministic demos. | every example. |
| `load_telco.py` | Loader: reads either CSV and adds `renewal_id`, `current_state`, `expected_path`, `window_open_at`. | every example. |
| `renewals.csv` | **Derived from Telco**: one renewal per customer in the subset, projected into the talk's state machine. | P5, contract-renewal. |
| `events.jsonl` | Hand-crafted — 36 events that exercise the specific failure modes in the talk (gate-denied discount, contract merger, mid-flight EOL, saga rollback). | P3. |
| `policy.yaml` | Hand-crafted — versioned renewal policy with discount caps, throttle, escalation rules. | P4, P6. |
| `expected_outputs/` | Captured stdout from a fresh run of every example. | regression checks. |
| `SOURCES.md` | Provenance, licenses, fetch URLs, fetch date. | citation. |

## The real-data path distribution

Projecting the 100-row Telco subset through `load_telco.infer_expected_path()` gives:

```
renewed                 44
renewed_with_offer      27
churned                 23
restructured             4
escalated                2
```

On the full 7,043-row corpus the same heuristic yields:

```
renewed               2858
renewed_with_offer    2053
churned               1655
restructured           263
escalated              214
```

The 23–26% churn rate matches the well-known headline churn rate for this dataset, and the small-but-nonzero `restructured` and `escalated` counts give every runtime pattern at least a handful of cases to fire on.

## Scenarios derived from the dataset

The five expected paths correspond to specific runtime-pattern failure modes:

| `expected_path` | What the patterns do |
|---|---|
| `renewed` | Happy path. P1 dispatches three sub-agents, P5 transitions `window_open → scoring → offer_sent → closed`, P4 gate allows all writes. |
| `renewed_with_offer` | P1 + P2 fan out; offer drafted within policy; P5 closes with `discount_pct ≤ 30`. |
| `restructured` | High-MRR Month-to-month account. Mid-flight P3 event (`plan_change_request`) reroutes the row through `human_required` and back to `closed` with a different plan. |
| `churned` | Customer didn't accept. P5 timer fires `offer_sent → expired`. |
| `escalated` | Either a surprising churn on a longer-term contract OR a hallucinated >30% discount. P4 gate denies, P6 routes to a specialist. |

## Reproducibility

```bash
# 1. Re-derive renewals.csv from the Telco subset
python data/load_telco.py        # prints the path distribution

# 2. Re-run any pattern
python patterns/p5-shared-state-machine/langgraph_example.py

# 3. Run the contract-renewal example end-to-end
python examples/contract-renewal/run.py

# 4. Regression-check against the canonical trace
diff <(python examples/contract-renewal/run.py) data/expected_outputs/contract-renewal__run.txt
```

See [`SOURCES.md`](SOURCES.md) for license, fetch URL, and fetch date.
