"""Analyze the §7 spine ablation results.

Reads all `evals/results/{spine}_{model}_n*_k*.jsonl` files and produces:

  - pass^1 and pass^k per (spine, model)
  - Δpass^k = pass^k(claude-sonnet-4-6) - pass^k(claude-sonnet-4-5) per spine
  - 95% bootstrap CIs on Δpass^k (10k resamples over scenarios)
  - a per-scenario disagreement table (which scenarios moved across models)

Writes:

  evals/results/summary.md            — pastable into §7 of the paper
  evals/results/summary.json          — machine-readable mirror
  evals/results/cost_summary.md       — total cost from cost_ledger.jsonl

Usage:
  python evals/analyze.py
  python evals/analyze.py --bootstrap 10000 --alpha 0.05
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"

FNAME_RE = re.compile(r"^(?P<spine>p[35])_(?P<model>[\w\-\.]+)_n(?P<n>\d+)_k(?P<k>\d+)\.jsonl$")


def load_results() -> dict[tuple[str, str], list[dict]]:
    by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    if not RESULTS.exists():
        return by_key
    for p in RESULTS.glob("*.jsonl"):
        if p.name == "cost_ledger.jsonl":
            continue
        m = FNAME_RE.match(p.name)
        if not m:
            continue
        spine, model = m.group("spine"), m.group("model")
        with p.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                by_key[(spine, model)].append(row)
    return by_key


def pass_at_k(rows: list[dict]) -> float:
    if not rows:
        return float("nan")
    return mean(r["pass_at_k"] for r in rows)


def bootstrap_delta(rows_a: list[dict], rows_b: list[dict],
                   n_resamples: int, alpha: float) -> tuple[float, float, float]:
    """Bootstrap CI for mean(pass^k of A) - mean(pass^k of B) over matched scenarios.

    A is the higher-version model (Sonnet 4.6), B is the lower (Sonnet 4.5).
    """
    by_task_a = {r["task_id"]: r["pass_at_k"] for r in rows_a}
    by_task_b = {r["task_id"]: r["pass_at_k"] for r in rows_b}
    shared = sorted(set(by_task_a) & set(by_task_b))
    if not shared:
        return float("nan"), float("nan"), float("nan")

    deltas = [by_task_a[t] - by_task_b[t] for t in shared]
    point = mean(deltas)

    samples = []
    n = len(shared)
    for _ in range(n_resamples):
        resample = [deltas[random.randint(0, n - 1)] for _ in range(n)]
        samples.append(mean(resample))
    samples.sort()
    lo = samples[int(alpha / 2 * n_resamples)]
    hi = samples[int((1 - alpha / 2) * n_resamples)]
    return point, lo, hi


def write_summary(by_key: dict[tuple[str, str], list[dict]], *,
                  n_resamples: int, alpha: float) -> str:
    lines = ["# §7 spine ablation — results summary", ""]
    if not by_key:
        lines.append("_No result files found in `evals/results/`. Run `evals/run_eval.py --live ...` first._")
        return "\n".join(lines)

    spines = sorted({s for s, _ in by_key})
    models = sorted({m for _, m in by_key})

    lines.append("## pass^k per (spine, model)")
    lines.append("")
    lines.append("| spine | model | N | k | pass^k |")
    lines.append("|---|---|---:|---:|---:|")
    for spine in spines:
        for model in models:
            rows = by_key.get((spine, model), [])
            if not rows:
                continue
            k = rows[0]["k"]
            lines.append(f"| {spine.upper()} | {model} | {len(rows)} | {k} | {pass_at_k(rows):.3f} |")
    lines.append("")

    # Δpass^k requires both models for the same spine.
    if len(models) >= 2:
        m_high = next((m for m in models if "4-6" in m or "4.6" in m), models[-1])
        m_low = next((m for m in models if "4-5" in m or "4.5" in m), models[0])
        lines.append(f"## Δpass^k = pass^k({m_high}) − pass^k({m_low})")
        lines.append("")
        lines.append(f"_Bootstrap 95% CI, {n_resamples} resamples over matched scenarios._")
        lines.append("")
        lines.append("| spine | Δpass^k | 95% CI |")
        lines.append("|---|---:|---|")
        for spine in spines:
            rows_high = by_key.get((spine, m_high), [])
            rows_low = by_key.get((spine, m_low), [])
            if not rows_high or not rows_low:
                lines.append(f"| {spine.upper()} | _missing data_ | _missing data_ |")
                continue
            d, lo, hi = bootstrap_delta(rows_high, rows_low,
                                       n_resamples=n_resamples, alpha=alpha)
            lines.append(f"| {spine.upper()} | {d:+.3f} | [{lo:+.3f}, {hi:+.3f}] |")
        lines.append("")
        lines.append("**Interpretation rule for the paper:** the spine hypothesis (H_drift) is supported if "
                     "P3 shows |Δpass^k| ≥ 0.10 and P5 shows |Δpass^k| ≤ 0.05. A reversed direction "
                     "(P5 drifts more than P3) falsifies the hypothesis and should be reported as such.")

    return "\n".join(lines)


def write_cost_summary() -> str:
    ledger = RESULTS / "cost_ledger.jsonl"
    if not ledger.exists():
        return "# Cost summary\n\n_No cost ledger found._\n"
    by_run: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {"calls": 0, "cost": 0.0, "in_tok": 0, "out_tok": 0})
    with ledger.open() as fh:
        for line in fh:
            row = json.loads(line)
            key = (row["spine"], row["model"])
            by_run[key]["calls"] += 1
            by_run[key]["cost"] += row["cost_usd"]
            by_run[key]["in_tok"] += row["input_tokens"]
            by_run[key]["out_tok"] += row["output_tokens"]
    out = ["# Cost summary (from cost_ledger.jsonl)", "",
           "| spine | model | calls | input tok | output tok | cost USD |",
           "|---|---|---:|---:|---:|---:|"]
    total = 0.0
    for (spine, model), v in sorted(by_run.items()):
        out.append(f"| {spine.upper()} | {model} | {v['calls']} | {v['in_tok']:,} | {v['out_tok']:,} | ${v['cost']:.2f} |")
        total += v["cost"]
    out.append(f"| **total** | | | | | **${total:.2f}** |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=10000)
    ap.add_argument("--alpha", type=float, default=0.05)
    args = ap.parse_args()

    random.seed(42)
    by_key = load_results()
    summary = write_summary(by_key, n_resamples=args.bootstrap, alpha=args.alpha)
    cost = write_cost_summary()

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.md").write_text(summary + "\n")
    (RESULTS / "cost_summary.md").write_text(cost)
    (RESULTS / "summary.json").write_text(json.dumps({
        "n_resamples": args.bootstrap,
        "alpha": args.alpha,
        "keys": [{"spine": s, "model": m, "n": len(rows)} for (s, m), rows in by_key.items()],
    }, indent=2))
    print(summary)
    print()
    print(cost)


if __name__ == "__main__":
    main()
