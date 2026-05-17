"""P5 spine wrapper — durable row + CAS, LLM proposes next transition.

This is the "narrow proposal" spine. The LLM sees only:
  - the current Row (state, version, data, scenario context)
  - the set of ALLOWED_TRANSITIONS from the current state
  - the policy doc
  - the user intent

It returns a single JSON object: {"to_state": "...", "data_patch": {...}, "reason": "..."}

The wrapper then walks that proposal through Store.cas_transition, which raises
on illegal transitions or stale versions. The hypothesis (H_drift) is that this
narrow shape is robust across model versions because the model only chooses among
a tiny set of legal next states, and the predicate ("is this transition legal?")
lives in deterministic Python, not in the prompt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "patterns"))
sys.path.insert(0, str(HERE / "evals"))

from _common import log  # noqa: E402
from tau_bench_adapter import RenewalAgent, RenewalAgentState  # noqa: E402
from llm_client import LLMClient  # noqa: E402

# Reuse the canonical state machine from the pattern example.
sys.path.insert(0, str(HERE / "patterns" / "p5-shared-state-machine"))
from langgraph_example import ALLOWED_TRANSITIONS as _CANONICAL_TRANSITIONS  # noqa: E402

# The data layer (`data/load_telco.py:initial_state_for`) emits scenarios with
# `state ∈ {"init", "window_open", "scoring"}`. The canonical state machine in
# the pattern example starts at "pending". We extend the transition map with
# data-layer aliases so a fresh scenario's first turn has a legal proposal
# instead of falling into a terminal-state stop.
SPINE_ALLOWED_TRANSITIONS = {
    "init":        {"scoring"},
    "pending":     {"scoring"},
    "window_open": {"scoring"},
    **_CANONICAL_TRANSITIONS,
}
ALLOWED_TRANSITIONS = SPINE_ALLOWED_TRANSITIONS  # backward-compatible name


SYSTEM_PROMPT = """You are the renewal agent for a telco carrier.

You operate against a durable state machine. The current state and the set of
ALLOWED transitions from that state will be given to you on every turn. You
propose exactly ONE transition per turn, as a JSON object on a single line:

  {"to_state": "<one of the allowed transitions>", "data_patch": {<optional>}, "reason": "<short>"}

Hard constraints:
- Only choose a `to_state` that appears in ALLOWED_TRANSITIONS for the current state.
- Discounts above 30% must route through `human_required`, not directly to `offer_sent`.
- Contract mergers must route through `human_required`.
- When you have nothing useful left to propose, emit {"to_state": "stop", "reason": "..."}.

Return only the JSON object. No code fences, no prose.
"""


class P5SpineAgent(RenewalAgent):
    """RenewalAgent + LLM proposer that respects the state-machine spine."""

    def __init__(self, client: LLMClient, **overrides):
        super().__init__(**overrides)
        self.client = client
        self._trial_id: int = 0
        self._scenario_id: str = "unknown"

    def bind(self, *, scenario_id: str, trial: int) -> "P5SpineAgent":
        self._scenario_id = scenario_id
        self._trial_id = trial
        return self

    # --- Override the LLM-shaped half of the boundary ---------------------

    def _propose_action(self, obs: dict[str, Any]) -> dict[str, Any]:
        cur_state = self._state.state if self._state else "init"
        allowed = sorted(ALLOWED_TRANSITIONS.get(cur_state, set()))
        if not allowed:
            return {"type": "stop", "reason": f"terminal_state:{cur_state}"}

        user_prompt = _format_user_prompt(
            obs=obs,
            cur_state=cur_state,
            allowed_transitions=allowed,
            audit=self._state.audit if self._state else [],
        )
        result = self.client.propose(
            system=SYSTEM_PROMPT,
            user=user_prompt,
            scenario_id=self._scenario_id,
            trial=self._trial_id,
        )
        proposed = result.parsed

        to_state = proposed.get("to_state", "stop")
        if to_state == "stop":
            return {"type": "stop", "reason": proposed.get("reason", "model_stop")}
        if to_state not in allowed:
            log("p5", "model proposed illegal transition; stopping",
                to_state=to_state, allowed=allowed)
            return {"type": "stop", "reason": f"illegal_transition:{to_state}"}

        # Map state-machine transition to a tau_bench-style action so the
        # existing _gate / env.step pipeline keeps working.
        action = _transition_to_action(to_state, proposed.get("data_patch", {}), obs)
        # Update P5 spine row state alongside the env step. The gate runs after.
        if self._state is not None:
            self._state.state = to_state
        return action


def _format_user_prompt(*, obs: dict[str, Any], cur_state: str,
                       allowed_transitions: list[str], audit: list[dict[str, Any]]) -> str:
    return json.dumps({
        "current_state": cur_state,
        "allowed_transitions": allowed_transitions,
        "observation": obs,
        "audit_summary": [
            {"step": a.get("step"), "action_type": a.get("action", {}).get("type"),
             "reward": a.get("reward")}
            for a in audit[-5:]
        ],
        "instruction": "Propose exactly one transition as JSON.",
    }, indent=2)


def _transition_to_action(to_state: str, data_patch: dict[str, Any],
                         obs: dict[str, Any]) -> dict[str, Any]:
    """Translate a state-machine transition into a tau_bench action dict.

    The state names align with the actions the env knows how to handle. We keep
    the mapping explicit rather than guessing.
    """
    if to_state == "scoring":
        return {"type": "score_churn", "customer_id": obs.get("customer_id")}
    if to_state == "offer_sent":
        return {"type": "publish_offer", "discount_pct": data_patch.get("discount_pct", 15)}
    if to_state == "human_required":
        return {"type": "request_human_review", "reason": data_patch.get("reason", "policy")}
    if to_state == "closed":
        return {"type": "accept_renewal"}
    if to_state == "expired":
        return {"type": "expire_renewal"}
    return {"type": "stop", "reason": f"unmapped_state:{to_state}"}
