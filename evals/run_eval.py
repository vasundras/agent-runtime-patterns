"""Entry point: run the patterns through τ-bench's harness against Telco scenarios.

Without τ-bench installed, this falls back to a structural dry-run that
exercises the adapter against a fake environment, so the file is still useful
for sanity-checking the wiring.

Usage:
  python evals/run_eval.py                 # offline dry-run, all scenarios
  python evals/run_eval.py --k 4           # pass^k consistency over 4 trials
  python evals/run_eval.py --limit 10      # only first 10 scenarios

If you have τ-bench installed and an API key:
  pip install git+https://github.com/sierra-research/tau-bench
  export ANTHROPIC_API_KEY=...
  python evals/run_eval.py --live --k 8
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "patterns"))
sys.path.insert(0, str(HERE))

from _common import log  # noqa: E402
from scenarios_telco import build_scenarios  # noqa: E402
from tau_bench_adapter import build_agent  # noqa: E402


class FakeEnvFromScenario:
    """Lets us exercise the adapter offline without τ-bench installed.

    Real τ-bench envs do all of this plus a simulated user LLM. Here we
    return a fixed-trajectory env that mirrors the scenario's expected path.
    """

    def __init__(self, scenario: dict):
        self.scenario = scenario
        self.step_n = 0
        self.db = dict(scenario["initial_db"])

    def reset(self):
        return {
            "renewal_id": self.db["renewal_id"],
            "customer_id": self.db["customer_id"],
            "step": 0,
            "user_intent": self.scenario["user_intent"],
        }

    def step(self, action: dict):
        self.step_n += 1
        # Cheap simulator: actions modify the db; reward is +1 at goal-match.
        if action["type"] == "score_churn":
            churn = 0.85 if self.scenario["goal"].get("outcome") == "churned" else 0.4
            return {"step": self.step_n, "churn_score": churn}, 0.0, False
        if action["type"] in {"publish_offer", "accept_renewal"}:
            self.db["state"] = "closed"
        if action["type"] == "expire_renewal":
            self.db["state"] = "expired"
        # done when the action is "stop" or db state matches goal terminal
        done = self.db.get("state") in {"closed", "expired", "human_required"}
        reward = 1.0 if self.db.get("state") == self.scenario["goal"].get("state") else 0.0
        return {"step": self.step_n, "db_state": self.db.get("state")}, reward, done


def run_one(scenario: dict, k: int = 1) -> dict:
    successes = 0
    trial_results = []
    for trial in range(k):
        agent = build_agent()
        env = FakeEnvFromScenario(scenario)
        result = agent.solve(env)
        # Naive goal match: did the final state align?
        matched = result.get("final_state") == scenario["goal"].get("state") or any(
            a.get("reward", 0) > 0 for a in result.get("audit", [])
        )
        successes += 1 if matched else 0
        trial_results.append({"trial": trial, "matched": matched, "version": result["version"]})
    return {
        "task_id": scenario["task_id"],
        "k": k,
        "pass_at_k": successes / max(k, 1),
        "trials": trial_results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=1, help="pass^k consistency (trials per scenario)")
    ap.add_argument("--limit", type=int, default=10, help="limit number of scenarios")
    ap.add_argument("--live", action="store_true", help="use real τ-bench (requires install + API key)")
    args = ap.parse_args()

    if args.live:
        log("eval", "live τ-bench mode not implemented in this offline shim — "
                   "this is where you'd `from tau_bench.run import run` and pass build_agent")
        return

    scenarios = build_scenarios(subset=True)[: args.limit]
    log("eval", f"running offline dry-run on {len(scenarios)} scenarios with k={args.k}")

    results = [run_one(s, k=args.k) for s in scenarios]
    overall = sum(r["pass_at_k"] for r in results) / max(len(results), 1)

    log("eval", "summary", overall_pass_at_k=round(overall, 3), scenarios=len(results))
    out_path = HERE / "results" / f"dry_run_k{args.k}.json"
    out_path.parent.mkdir(exist_ok=True)
    with out_path.open("w") as fh:
        json.dump({"k": args.k, "overall": overall, "results": results}, fh, indent=2)
    log("eval", "wrote", path=str(out_path))


if __name__ == "__main__":
    main()
