"""Run the entire §7 spine ablation end-to-end, unattended.

This is the single command you launch when you want to walk away and come back
to results. Calls `run_eval.py` for each (spine, model, N, k) cell in the
schedule. Every cell is resumable — if the process dies mid-run, re-launching
this script picks up where it left off without re-spending on completed scenarios.

Usage:

  # Local Mac, unattended overnight:
  caffeinate -i nohup python evals/run_full_ablation.py \\
      --results-dir ~/agent-runtime-results \\
      --stage all \\
      > ~/agent-runtime-results/run.log 2>&1 &

  # Colab cell:
  !python evals/run_full_ablation.py \\
      --results-dir /content/drive/MyDrive/agent-runtime-results \\
      --stage smoke   # then lean, then full

  # Resume after interruption (same command as the original run):
  python evals/run_full_ablation.py --results-dir <same> --stage <same>

Stages:
  smoke   — 5 scenarios, k=1, P5, Sonnet 4.6 (≈$5)
  lean    — 30 scenarios, k=4, both spines, both models (≈$72-120)
  full    — 100 scenarios, k=4, both spines, both models (≈$240-400)
  all     — smoke → lean → full, with a decision gate between lean and full

The decision gate prints the lean Δpass^k. If you set `--auto-proceed`, the
script continues to full automatically; otherwise it stops at the gate so you
can inspect numbers before paying for the full run.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent


def _cell_cmd(*, spine: str, model: str, limit: int, k: int, results_dir: Path,
              live: bool, mock: bool) -> list[str]:
    cmd = [sys.executable, str(HERE / "run_eval.py"),
           "--spine", spine, "--model", model,
           "--limit", str(limit), "--k", str(k),
           "--results-dir", str(results_dir)]
    if live:
        cmd.append("--live")
    if mock:
        cmd.append("--mock")
    return cmd


def run_cell(*, spine: str, model: str, limit: int, k: int, results_dir: Path,
             live: bool, mock: bool) -> int:
    """Sequentially: invoke run_eval.py for one cell, stream output to terminal."""
    cmd = _cell_cmd(spine=spine, model=model, limit=limit, k=k,
                    results_dir=results_dir, live=live, mock=mock)
    print(f"\n=== Cell: spine={spine} model={model} N={limit} k={k} live={live} mock={mock} ===")
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def run_cells_parallel(cell_specs: list[dict], *, results_dir: Path,
                       live: bool, mock: bool) -> int:
    """Launch all cells as background subprocesses, tee each to its own log file,
    wait for all, return non-zero if any failed.

    Per-cell log: {results_dir}/_logs/{spine}_{model}.log
    """
    log_dir = results_dir / "_logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    procs: list[tuple[dict, subprocess.Popen, Any]] = []
    print(f"\n=== Launching {len(cell_specs)} cells in parallel ===")
    for spec in cell_specs:
        cmd = _cell_cmd(results_dir=results_dir, live=live, mock=mock, **spec)
        log_name = f"{spec['spine']}_{spec['model']}.log"
        log_path = log_dir / log_name
        print(f"  → {spec['spine']} {spec['model']} N={spec['limit']} k={spec['k']}  →  {log_path}")
        log_fh = log_path.open("w", buffering=1)  # line-buffered
        log_fh.write(f"# cmd: {' '.join(cmd)}\n")
        log_fh.flush()
        proc = subprocess.Popen(cmd, stdout=log_fh, stderr=subprocess.STDOUT)
        procs.append((spec, proc, log_fh))

    # Progress poll while waiting.
    print(f"\n=== Waiting for {len(procs)} cells to finish (tail logs in {log_dir}) ===")
    print(f"=== Monitor with: tail -f {log_dir}/*.log ===\n")

    t0 = time.time()
    last_print = 0.0
    while any(p.poll() is None for _, p, _ in procs):
        time.sleep(5)
        # Print combined status every 30s.
        if time.time() - last_print > 30:
            elapsed = int(time.time() - t0)
            for spec, proc, _ in procs:
                jsonl_name = f"{spec['spine']}_{spec['model'].replace('/', '-')}_n{spec['limit']}_k{spec['k']}.jsonl"
                jsonl_path = results_dir / jsonl_name
                n_done = 0
                if jsonl_path.exists():
                    with jsonl_path.open() as fh:
                        n_done = sum(1 for _ in fh)
                status = "DONE" if proc.poll() is not None else "running"
                print(f"  [{elapsed:4d}s] {spec['spine']} {spec['model']}: {n_done}/{spec['limit']} {status}")
            print()
            last_print = time.time()

    # Final reap.
    last_rc = 0
    for spec, proc, log_fh in procs:
        rc = proc.wait()
        log_fh.close()
        if rc != 0:
            print(f"  ! cell failed: {spec['spine']} {spec['model']} rc={rc} — see log")
            last_rc = last_rc or rc
        else:
            print(f"  ✓ cell done:   {spec['spine']} {spec['model']}")
    print(f"\n=== Parallel batch done in {int(time.time() - t0)}s ===")
    return last_rc


def smoke(results_dir: Path, *, live: bool, mock: bool) -> int:
    """5 scenarios, k=1, P5 only, Sonnet 4.6. Confirms the harness round-trips."""
    return run_cell(spine="p5", model="claude-sonnet-4-6", limit=5, k=1,
                    results_dir=results_dir, live=live, mock=mock)


def _lean_specs() -> list[dict]:
    return [
        {"spine": "p5", "model": "claude-sonnet-4-6", "limit": 30, "k": 4},
        {"spine": "p3", "model": "claude-sonnet-4-6", "limit": 30, "k": 4},
        {"spine": "p5", "model": "claude-sonnet-4-5", "limit": 30, "k": 4},
        {"spine": "p3", "model": "claude-sonnet-4-5", "limit": 30, "k": 4},
    ]


def _full_specs() -> list[dict]:
    return [
        {"spine": "p5", "model": "claude-sonnet-4-6", "limit": 100, "k": 4},
        {"spine": "p3", "model": "claude-sonnet-4-6", "limit": 100, "k": 4},
        {"spine": "p5", "model": "claude-sonnet-4-5", "limit": 100, "k": 4},
        {"spine": "p3", "model": "claude-sonnet-4-5", "limit": 100, "k": 4},
    ]


def lean(results_dir: Path, *, live: bool, mock: bool, parallel: bool) -> int:
    """30 scenarios, k=4, both spines, both models."""
    specs = _lean_specs()
    if parallel:
        return run_cells_parallel(specs, results_dir=results_dir, live=live, mock=mock)
    last_rc = 0
    for s in specs:
        rc = run_cell(results_dir=results_dir, live=live, mock=mock, **s)
        last_rc = last_rc or rc
    return last_rc


def full(results_dir: Path, *, live: bool, mock: bool, parallel: bool) -> int:
    """100 scenarios, k=4, both spines, both models."""
    specs = _full_specs()
    if parallel:
        return run_cells_parallel(specs, results_dir=results_dir, live=live, mock=mock)
    last_rc = 0
    for s in specs:
        rc = run_cell(results_dir=results_dir, live=live, mock=mock, **s)
        last_rc = last_rc or rc
    return last_rc


def show_summary(results_dir: Path) -> None:
    """Run analyze.py and dump the summary to stdout."""
    print("\n=== Current results summary ===")
    subprocess.call([sys.executable, str(HERE / "analyze.py"),
                     "--results-dir", str(results_dir)])


def decision_gate(results_dir: Path, *, auto_proceed: bool) -> bool:
    """Show lean numbers and ask whether to continue to full.

    Returns True to proceed. With --auto-proceed, always returns True after
    showing the table. Without it, the script exits and the user re-launches
    with --stage full once they've decided.
    """
    print("\n=== DECISION GATE — review lean Δpass^k before paying for full ===")
    show_summary(results_dir)
    if auto_proceed:
        print("\n--auto-proceed set → continuing to full.")
        return True
    print("\nNot auto-proceeding. To continue to full, re-launch with:")
    print(f"  python evals/run_full_ablation.py --results-dir {results_dir} --stage full --live")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", required=True,
                    help="root dir for all JSONL files (use a Drive mount on Colab, or a stable dir on local Mac)")
    ap.add_argument("--stage", choices=["smoke", "lean", "full", "all", "summary"], default="all",
                    help="which stage to run (default all = smoke → lean → gate → full)")
    ap.add_argument("--live", action="store_true",
                    help="use real Anthropic API (requires ANTHROPIC_API_KEY)")
    ap.add_argument("--mock", action="store_true",
                    help="use MockLLMClient (no API calls, structural check)")
    ap.add_argument("--auto-proceed", action="store_true",
                    help="skip the human gate between lean and full")
    ap.add_argument("--parallel", action="store_true",
                    help="run the 4 cells of lean/full concurrently as background processes. "
                         "Wall clock drops ~4x; total cost is unchanged. Recommended for live runs.")
    args = ap.parse_args()

    if not args.live and not args.mock:
        print("WARNING: neither --live nor --mock set. The run will not actually call the LLM.")
        print("         Pass --live for the real experiment, --mock for a structural check.")

    results_dir = Path(args.results_dir).expanduser().resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    # Make sure run_eval.py and the cost ledger end up in the same dir.
    os.environ["EVAL_RESULTS_DIR"] = str(results_dir)

    # Persist a small manifest so we can tell from logs what was launched.
    (results_dir / "run_manifest.json").write_text(json.dumps({
        "ts": time.time(),
        "stage": args.stage,
        "live": args.live,
        "mock": args.mock,
        "argv": sys.argv,
    }, indent=2))

    t0 = time.time()

    if args.stage == "summary":
        show_summary(results_dir)
        return

    if args.stage in ("smoke", "all"):
        rc = smoke(results_dir, live=args.live, mock=args.mock)
        if rc != 0:
            print(f"smoke stage failed rc={rc}; aborting before lean.")
            sys.exit(rc)

    if args.stage in ("lean", "all"):
        rc = lean(results_dir, live=args.live, mock=args.mock, parallel=args.parallel)
        if rc != 0:
            print(f"lean stage failed rc={rc}; aborting before full.")
            sys.exit(rc)

    if args.stage == "all":
        if not decision_gate(results_dir, auto_proceed=args.auto_proceed):
            return

    if args.stage in ("full", "all"):
        rc = full(results_dir, live=args.live, mock=args.mock, parallel=args.parallel)
        if rc != 0:
            print(f"full stage failed rc={rc}.")

    show_summary(results_dir)
    print(f"\nTotal wall time: {int(time.time() - t0)}s")
    print(f"Results dir: {results_dir}")


if __name__ == "__main__":
    main()
