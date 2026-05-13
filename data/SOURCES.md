# Data sources

## Primary: IBM Telco Customer Churn

- **Files**: `telco_customer_churn_full.csv` (7,043 rows), `telco_customer_churn_subset.csv` (100 rows, fixed sample).
- **Origin**: IBM Cognos Analytics Sample Data, originally published as part of the IBM Watson Analytics "Customer Churn" guided tutorial (circa 2017).
- **Mirrors**: Distributed widely — Kaggle (`blastchar/telco-customer-churn`), IBM Developer GitHub samples, scikit-learn community examples.
- **License**: IBM Sample Data Set terms — free to use, redistribute, and modify; widely treated as effectively public-domain by the community. Many redistributions explicitly re-license as CC0.
- **Shape**: 7,043 customers × 21 columns. Includes `customerID`, demographic (`gender`, `SeniorCitizen`, `Partner`, `Dependents`), tenure (`tenure` in months), services (Phone, Internet, Streaming, etc.), billing (`Contract` ∈ {Month-to-month, One year, Two year}, `MonthlyCharges`, `TotalCharges`), and the churn label `Churn` ∈ {Yes, No}.
- **Why this dataset for this repo**: every pattern in the talk targets contract-renewal / churn-prevention workflows. The Telco dataset is the de-facto industry benchmark for that problem space, has the right column shape (`Contract`, `tenure`, `MonthlyCharges`, `Churn`), and is recognized at sight by every reviewer who has worked in telecom or CRM ML. ~26.5% real churn rate gives the runtime patterns a realistic mix of happy paths and failure paths to exercise.

### How we project Telco rows into renewals

`data/load_telco.py` adds four derived columns:

- `renewal_id` — `r-` + `md5(customerID)[:8]`. Stable across runs.
- `current_state` — heuristic from `(Contract, tenure)`: Month-to-month → `scoring`; longer contracts close to renewal → `window_open`; otherwise `init`.
- `expected_path` — heuristic from `(Churn, Contract, MonthlyCharges)` so each scenario in `examples/contract-renewal/` exercises a different pattern's failure mode (renewed / renewed_with_offer / restructured / churned / escalated).
- `window_open_at` — synthetic anchor date derived from tenure.

The original 21 columns are preserved verbatim.

## Eval target: τ-bench

- **Files**: see `evals/` directory.
- **Origin**: Sierra + Stanford NLP, *"τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains"* (Yao et al., 2024). arXiv `2406.12045`.
- **Repo**: https://github.com/sierra-research/tau-bench
- **License**: Apache 2.0.
- **Why this for evals**: τ-bench scenarios (retail, airline) are the closest public match to the runtime patterns we describe — multi-turn, tool-using agents under policy constraints, deterministic ground-truth checks against external state. Exactly the eval harness slide 18 of the talk gestures at.

## Synthetic stays in place for

- `events.jsonl` — keeps the talk's specific failure scenarios (gate-denied 90% discount, contract merger, mid-flight EOL, saga rollback) which the Telco dataset alone doesn't surface. These are intentionally crafted to exercise specific runtime-pattern failure modes.
- `policy.yaml` — there is no canonical public "renewal policy" so this is hand-crafted, with version tag, to demo the gate.

## Reproducibility

The full Telco CSV was fetched on **2026-05-13** from:

```
https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv
```

Row count and SHA256 of the file at fetch time:

```bash
$ wc -l data/telco_customer_churn_full.csv
7044 data/telco_customer_churn_full.csv
$ sha256sum data/telco_customer_churn_full.csv
# (run on your end to confirm)
```

If the file ever changes upstream, the loader still works — the `expected_path` distribution will shift but the schema is stable.
