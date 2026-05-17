"""Entry point: run the spine ablation against Telco scenarios.

Three modes:

  # Offline structural dry-run (no API key required):
  python evals/run_eval.py --limit 10 --k 1

  # Smoke test against the real Anthropic API:
  python evals/run_eval.py --live --spine p5 --model claude-sonnet-4-6 \\
      --limit 5 --k 1

  # Lean run (one of the four-evening cells):
  python evals/run_eval.py --live --spine p5 --model claude-sonnet-4-6 \\
      --limit 30 --k 4

Outputs:
  evals/results/{spine}_{model}_n{N}_k{K}.jsonl     # one JSON line per scenario
  evals/results/cost_ledger.jsonl                   # one line per LLM call

See ABLATION_TIMELINE.md for the full four-evening plan and expected costs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "patterns"))
sys.path.insert(0, str(HERE))

from _common import log  # noqa: E402
from scenarios_telco import build_scenarios  # noqa: E402
from tau_bench_adapter import build_agent  # noqa: E402


class DeterministicEnv:
    """Single-LLM env: the spine's LLM is the only stochastic component.

    We intentionally do NOT spin up a simulated user via a second LLM, because
    we want the §7 Δpass^k to be attributable to the spine + model under test,
    not to a moving user-side model. The env is deterministic and goal-shaped.
    """

    def __init__(self, scenario: dict):
        self.scenario = scenario
        self.step_n = 0
        self.db = dict(scenario["initial_db"])
        self._churn_seed = 0.85 if scenario["goal"].get("outcome") in {"churned", "escalated"} else 0.4

    def reset(self):
        return {
            "renewal_id": self.db["renewal_id"],
            "customer_id": self.db["customer_id"],
            "tenure": self.db.get("tenure"),
            "monthly_charges": self.db.get("monthly_charges"),
            "contract": self.db.get("contract"),
            "step": 0,
            "user_intent": self.scenario["user_intent"],
            "policy_doc_summary": "Renewal v7: max 30% auto, mergers→human, M2M tenure>=12 may offer annual.",
            "goal_hint": None,  # we don't leak the goal to the agent
        }

    def step(self, action: dict):
        self.step_n += 1
        a_type = action.get("type")

        obs: dict[str, Any] = {"step": self.step_n}
        if a_type == "score_churn":
            obs["churn_score"] = self._churn_seed
        elif a_type == "draft_offer":
            obs["draft_status"] = "drafted"
            self.db["last_discount"] = action.get("discount_pct", 0)
        elif a_type in {"publish_offer", "accept_renewal"}:
            self.db["state"] = "closed"
            obs["renewal_state"] = "closed"
        elif a_type == "expire_renewal":
            self.db["state"] = "expired"
            obs["renewal_state"] = "expired"
        elif a_type == "request_human_review":
            self.db["state"] = "human_required"
            obs["renewal_state"] = "human_required"
        elif a_type == "stop":
            obs["agent_stop"] = True

        done = a_type == "stop" or self.db.get("state") in {"closed", "expired", "human_required"}
        reward = 1.0 if self.db.get("state") == self.scenario["goal"].get("state") else 0.0
        obs["user_intent"] = self.scenario["user_intent"]  # keep visible across turns
        return obs, reward, done


# --- Spine selection ------------------------------------------------------

def make_agent(spine: str, *, model: str | None, live: bool, mock: bool = False):
    """Returns a callable that builds a fresh agent per trial.

    Three modes:
      - mock=True       → use MockLLMClient (no API calls, scripted responses)
                          to exercise the spine code path offline.
      - live=True       → use real LLMClient with Anthropic SDK.
      - neither         → use the stub _propose_action in tau_bench_adapter
                          (legacy offline path that does not exercise the spine).
    """
    if mock:
        from llm_client import MockLLMClient, default_ledger
        ledger = default_ledger(spine=spine, model=model or "mock")
        if spine == "p5":
            from spines.p5_state_machine import P5SpineAgent

            def builder():
                client = MockLLMClient(model=model or "mock", spine="p5", ledger=ledger)
                return P5SpineAgent(client=client)
            return builder
        if spine == "p3":
            from spines.p3_event_driven import P3SpineAgent

            def builder():
                client = MockLLMClient(model=model or "mock", spine="p3", ledger=ledger)
                return P3SpineAgent(client=client)
            return builder
        raise ValueError(f"unknown spine: {spine}")

    if not live:
        # legacy offline shim — uses the stub _propose_action in tau_bench_adapter
        def builder():
            return build_agent()
        return builder

    from llm_client import LLMClient, default_ledger
    ledger = default_ledger(spine=spine, model=model or "unknown")

    if spine == "p5":
        from spines.p5_state_machine import P5SpineAgent

        def builder():
            client = LLMClient(model=model, spine="p5", ledger=ledger)
            return P5SpineAgent(client=client)
        return builder

    if spine == "p3":
        from spines.p3_event_driven import P3SpineAgent

        def builder():
            client = LLMClient(model=model, spine="p3", ledger=ledger)
            return P3SpineAgent(client=client)
        return builder

    raise ValueError(f"unknown spine: {spine}")


def run_one(scenario: dict, *, k: int, agent_builder, spine: str) -> dict:
    successes = 0
    trial_results = []
    for trial in range(k):
        agent = agent_builder()
        if hasattr(agent, "bind"):
            agent.bind(scenario_id=scenario["task_id"], trial=trial)
        env = DeterministicEnv(scenario)
        result = agent.solve(env)
        matched = result.get("final_state") == scenario["goal"].get("state") or any(
            a.get("reward", 0) > 0 for a in result.get("audit", [])
        )
        successes += 1 if matched else 0
        trial_results.append({
            "trial": trial,
            "matched": matched,
            "version": result.get("version"),
            "final_state": result.get("final_state"),
            "n_audit": len(result.get("audit", [])),
        })
    return {
        "task_id": scenario["task_id"],
        "spine": spine,
        "goal_state": scenario["goal"].get("state"),
        "k": k,
        "pass_at_k": successes / max(k, 1),
        "trials": trial_results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", choices=["p3", "p5"], default="p5",
                    help="which spine wrapper to use (--live only)")
    ap.add_argument("--model", default="claude-sonnet-4-6",
                    help="anthropic model identifier (--live only)")
    ap.add_argument("--k", type=int, default=1, help="pass^k consistency (trials per scenario)")
    ap.add_argument("--limit", type=int, default=10, help="limit number of scenarios")
    ap.add_argument("--live", action="store_true",
                    help="use real Anthropic API (requires ANTHROPIC_API_KEY)")
    ap.add_argument("--mock", action="store_true",
                    help="use MockLLMClient to exercise the spine path offline (no API calls)")
    ap.add_argument("--out", default=None,
                    help="output JSONL path (default: results/{spine}_{model}_n{N}_k{K}.jsonl)")
    args = ap.parse_args()

    scenarios = build_scenarios(subset=True)[: args.limit]
    mode = "LIVE" if args.live else ("MOCK" if args.mock else "OFFLINE")
    log("eval", f"mode={mode} spine={args.spine} model={args.model} N={len(scenarios)} k={args.k}")

    agent_builder = make_agent(args.spine, model=args.model, live=args.live, mock=args.mock)
    results = [run_one(s, k=args.k, agent_builder=agent_builder, spine=args.spine) for s in scenarios]
    overall = sum(r["pass_at_k"] for r in results) / max(len(results), 1)

    log("eval", "summary", overall_pass_at_k=round(overall, 3),
        scenarios=len(results), spine=args.spine, model=args.model)

    safe_model = (args.model or "stub").replace("/", "-")
    default_name = f"{args.spine}_{safe_model}_n{len(results)}_k{args.k}.jsonl"
    out_path = Path(args.out) if args.out else HERE / "results" / default_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")
    log("eval", "wrote", path=str(out_path))


if __name__ == "__main__":
    main()
