# Evals

> Slide 18 of the talk: **"Eval the patterns. Build the console first."**
> This directory holds the eval harness.

## Why τ-bench

We use [**τ-bench**](https://github.com/sierra-research/tau-bench) (Yao, Shinn, Razavi, Narasimhan — Sierra + Stanford, 2024) as the primary eval target. τ-bench is the closest public benchmark to what production agent runtimes actually need to measure:

- Multi-turn tool use against a stateful database.
- Explicit policy documents the agent must obey (the *gate* in our P4 pattern).
- The evaluator checks **end-state of the database**, not just the chat — exactly how P5 thinks about correctness.
- The `pass^k` metric measures **consistency across trials** — i.e. *drift*, which is the talk's headline failure mode.

τ-bench published two domains at launch (`retail`, `airline`) and the community has added more (healthcare, telco-like). For this repo we use `retail` as the canonical scenario because it's the closest match to the contract-renewal example: a customer-facing agent under policy, executing tool calls against an authoritative store, where failures are observable in the store's end state.

## Citation

```
Yao, S., Shinn, N., Razavi, P., & Narasimhan, K. (2024).
τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains.
arXiv:2406.12045 [cs.AI]. https://arxiv.org/abs/2406.12045
```

- **License (paper)**: CC BY 4.0.
- **License (code)**: MIT (per the repo at `sierra-research/tau-bench`).
- **Verified**: 2026-05-13.

## Mapping our six patterns onto τ-bench's eval surfaces

τ-bench gives us four kinds of evaluation per scenario. Slide 18 of the talk names four eval surfaces too — they line up almost perfectly:

| Talk surface (slide 18) | τ-bench surface | What our pattern catches |
|---|---|---|
| Single-step — "given this state, what action?" | One-turn tool selection accuracy | P1 sub-agent routing; P4 gate decisions |
| Trajectory — "replay a real renewal end-to-end" | Full conversation `pass@1` | P1+P2 end-to-end composition |
| Adversarial — "EOL event at the worst moment" | Pertubation-injected scenarios | P3 mid-flight events; P5 timer races |
| Production sample — "1,000 live renewals · human review" | `pass^k` (consistency over k trials) | The whole runtime; drift detection |

## Files

- [`tau_bench_adapter.py`](tau_bench_adapter.py) — a thin shim that lets you run a renewal agent built from this repo's patterns inside τ-bench's harness. It exposes a `RenewalAgent` class that conforms to τ-bench's expected interface and delegates tool-calls to P5's state machine + P4's gate.
- [`scenarios_telco.py`](scenarios_telco.py) — converts rows from `data/telco_customer_churn_subset.csv` into τ-bench-style task definitions (goal state, allowed tools, policy doc).
- [`run_eval.py`](run_eval.py) — entry point: `python evals/run_eval.py --scenario churn --k 8` runs `pass^k` against the IBM Telco subset.

## Quick start

```bash
# 1. Install tau-bench (it's pip-installable from the repo)
pip install git+https://github.com/sierra-research/tau-bench

# 2. Run the patterns through the eval harness
export ANTHROPIC_API_KEY=...
python evals/run_eval.py --domain retail --num-trials 8

# 3. Compare two model versions (drift detection — slide 21)
python evals/run_eval.py --domain retail --num-trials 8 --model claude-sonnet-4-5
python evals/run_eval.py --domain retail --num-trials 8 --model claude-sonnet-4-6
# diff the resulting JSON in evals/results/ to see drift vs. variance
```

## What this does *not* claim

- We are **not** publishing eval *numbers* in this repo. Numbers belong in a paper with rigor (see `arxiv/STRATEGY.md` Option C — "Drift Dominates Variance").
- We are publishing an **eval harness** that lets a reader reproduce the measurement on their own keys, their own model, their own scenarios.

This is the engineering equivalent of shipping the unit-test runner, not the test results.
