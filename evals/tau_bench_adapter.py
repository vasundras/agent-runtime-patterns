"""τ-bench adapter — wire the runtime patterns through Sierra's eval harness.

τ-bench expects an *Agent* class with a known interface (a `solve()` method that
takes an environment and returns a final state). We wrap the patterns from
`patterns/` so that:

  - P5 (state machine) backs the renewal_id row.
  - P4 (gate) inspects every tool call before it hits τ-bench's database.
  - P1 (orchestrator) routes sub-tasks (price-quote, plan-change, refund).
  - P6 (HITL) escalates when the policy gate denies an action.

This file is intentionally a *shim*. It runs end-to-end only if τ-bench is
installed; without it, the file imports cleanly and serves as documentation of
the contract between this repo and the eval harness.

Reference: Yao et al., "τ-bench: A Benchmark for Tool-Agent-User Interaction
in Real-World Domains", arXiv:2406.12045, 2024.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "patterns"))
from _common import log  # noqa: E402


def _tau_bench_available() -> bool:
    try:
        import tau_bench  # noqa: F401
        return True
    except ImportError:
        return False


# --- The contract our adapter has to satisfy --------------------------------
# τ-bench passes the agent an `env` with .reset(), .step(action), and .state.
# The agent returns the final database state. The harness then compares that
# end-state to the ground-truth goal state. This matches P5's view: the row
# IS the source of truth, and correctness is "did the row end up where it
# should have?"

@dataclass
class RenewalAgentState:
    """What P5 holds. Mirrors our state machine."""
    renewal_id: str
    state: str = "init"
    version: int = 0
    audit: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RenewalAgent:
    """Adapter that satisfies τ-bench's Agent interface using our patterns.

    Wiring:
      env.step(action) → P4.gate(action) → if allow: P5.cas(...) → record audit
                                         → if deny:  P6.escalate(...) → return early
    """
    policy_version: str = "v7"
    max_discount_pct: int = 30
    _state: RenewalAgentState | None = None

    # τ-bench-style `solve` method
    def solve(self, env: Any, max_steps: int = 30) -> dict[str, Any]:
        obs = env.reset()
        self._state = RenewalAgentState(renewal_id=obs.get("renewal_id", "r-unknown"))

        for step in range(max_steps):
            action = self._propose_action(obs)
            if action.get("type") == "stop":
                log("eval", "agent stop", step=step)
                break

            # P4 gate (synchronous policy check before any tool call)
            allowed, reason = self._gate(action)
            if not allowed:
                log("eval", "gate DENY → escalate", action=action.get("type"), reason=reason)
                self._state.audit.append({"step": step, "denied": action, "reason": reason})
                # P6: this is where in production we'd `suspend()` the workflow.
                break

            # Execute against τ-bench's environment
            obs, reward, done = env.step(action)
            # P5: every accepted tool-call is a state transition
            self._state.version += 1
            self._state.audit.append({"step": step, "action": action, "reward": reward})
            if done:
                break

        return {
            "renewal_id": self._state.renewal_id,
            "final_state": self._state.state,
            "version": self._state.version,
            "audit": self._state.audit,
            "policy_version": self.policy_version,
        }

    # --- Action selection (would be an LLM in production) ------------------

    def _propose_action(self, obs: dict[str, Any]) -> dict[str, Any]:
        """Stub: in real eval, an LLM proposes the next tool call from obs.

        Drives a minimal happy-path trajectory so the structural check exits
        cleanly: score → offer → publish → stop.
        """
        seen = {a["action"]["type"] for a in (self._state.audit if self._state else [])}
        if "score_churn" not in seen:
            return {"type": "score_churn", "customer_id": obs.get("customer_id")}
        if obs.get("churn_score", 0) > 0.6 and "draft_offer" not in seen:
            return {"type": "draft_offer", "discount_pct": 15}
        if "draft_offer" in seen and "publish_offer" not in seen:
            return {"type": "publish_offer"}
        return {"type": "stop"}

    # --- P4 · Gate ---------------------------------------------------------

    def _gate(self, action: dict[str, Any]) -> tuple[bool, str]:
        if action.get("type") == "draft_offer":
            if action.get("discount_pct", 0) > self.max_discount_pct:
                return False, f"discount {action['discount_pct']}% > max {self.max_discount_pct}%"
        if action.get("type") == "merge_contracts":
            return False, "contract_merger requires human (policy " + self.policy_version + ")"
        return True, "within envelope"


# --- Entry point used by tau-bench's runner ---------------------------------

def build_agent(**overrides) -> RenewalAgent:
    """τ-bench expects a builder function; this is ours."""
    return RenewalAgent(**overrides)


if __name__ == "__main__":
    log("init", "τ-bench adapter — self-test")
    if not _tau_bench_available():
        log("init", "tau-bench not installed — running offline structural check")
    agent = build_agent()
    # Use a fake env to demonstrate the shape end-to-end
    class FakeEnv:
        def __init__(self):
            self.step_n = 0
        def reset(self):
            return {"renewal_id": "r-fake-123", "customer_id": "C-001", "step": 0}
        def step(self, action):
            self.step_n += 1
            return {"churn_score": 0.72, "step": self.step_n}, 0.0, action["type"] == "stop"
    result = agent.solve(FakeEnv())
    log("eval", "self-test result", result=result)
