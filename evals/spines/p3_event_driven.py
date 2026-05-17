"""P3 spine wrapper — append-only event log, LLM consumes the log.

This is the "wide proposal" spine. The LLM sees the full event log (or a recent
window of it) plus the policy doc and the user intent, and is asked to interpret
what event to emit next:

  {"event_type": "...", "payload": {...}, "reason": "..."}

The wrapper then translates the proposed event into a tau_bench action and runs
it through the same gate the P5 spine uses. The hypothesis (H_drift) is that
this wider, more interpretive shape — "given everything that has happened,
what should I do next?" — drifts more across model versions than P5's narrow
"choose one of these legal transitions" shape.

Both spines share the same gate, audit, and terminal handling, so the only
intentional variable across the §7 ablation is the spine itself.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "patterns"))
sys.path.insert(0, str(HERE / "evals"))

from _common import log  # noqa: E402
from tau_bench_adapter import RenewalAgent  # noqa: E402
from llm_client import LLMClient  # noqa: E402

sys.path.insert(0, str(HERE / "patterns" / "p3-event-driven-sequencing"))
from langgraph_example import Event, EventLog  # noqa: E402


SYSTEM_PROMPT = """You are the renewal agent for a telco carrier.

You operate against an append-only event log. The full log so far (or a recent
window of it) will be given to you on every turn. You propose exactly ONE next
event per turn, as a JSON object on a single line:

  {"event_type": "<one of: score_churn|draft_offer|publish_offer|request_human_review|accept_renewal|expire_renewal|stop>",
   "payload": {<event-specific fields>},
   "reason": "<short justification>"}

Hard constraints:
- Discounts above 30% must produce a `request_human_review` event, not `draft_offer` / `publish_offer`.
- Contract mergers must produce a `request_human_review` event.
- Do not repeat an event you have already emitted (idempotency is enforced downstream, but repeating wastes turns).
- When the renewal is in a terminal state, or you have nothing useful to do, emit {"event_type": "stop", "reason": "..."}.

Return only the JSON object. No code fences, no prose.
"""


class P3SpineAgent(RenewalAgent):
    """RenewalAgent + LLM proposer that consumes an event log."""

    def __init__(self, client: LLMClient, log_window: int = 20, **overrides):
        super().__init__(**overrides)
        self.client = client
        self.log_window = log_window
        self.event_log = EventLog()
        self._trial_id: int = 0
        self._scenario_id: str = "unknown"

    def bind(self, *, scenario_id: str, trial: int) -> "P3SpineAgent":
        self._scenario_id = scenario_id
        self._trial_id = trial
        return self

    def _propose_action(self, obs: dict[str, Any]) -> dict[str, Any]:
        # Append the incoming observation as an event before proposing.
        self.event_log.append(Event(
            id=str(uuid.uuid4()),
            type="observation",
            payload={k: v for k, v in obs.items() if k != "user_intent"},
        ))

        user_prompt = _format_user_prompt(
            obs=obs,
            event_log=self.event_log,
            window=self.log_window,
        )
        result = self.client.propose(
            system=SYSTEM_PROMPT,
            user=user_prompt,
            scenario_id=self._scenario_id,
            trial=self._trial_id,
        )
        proposed = result.parsed

        event_type = proposed.get("event_type", "stop")
        if event_type == "stop":
            return {"type": "stop", "reason": proposed.get("reason", "model_stop")}

        # Record the proposed event in the log, then translate to action.
        payload = proposed.get("payload", {}) or {}
        self.event_log.append(Event(
            id=str(uuid.uuid4()),
            type=event_type,
            payload=payload,
        ))
        return _event_to_action(event_type, payload, obs)


def _format_user_prompt(*, obs: dict[str, Any], event_log: EventLog, window: int) -> str:
    log_window = [
        {"id": e.id[:8], "type": e.type, "payload": e.payload}
        for e in event_log.events[-window:]
    ]
    return json.dumps({
        "user_intent": obs.get("user_intent"),
        "event_log_recent": log_window,
        "event_log_size": len(event_log.events),
        "instruction": "Propose exactly one next event as JSON.",
    }, indent=2)


def _event_to_action(event_type: str, payload: dict[str, Any],
                    obs: dict[str, Any]) -> dict[str, Any]:
    """Translate an event proposal into a tau_bench action dict.

    Kept symmetric with P5's _transition_to_action so the env sees the same
    action surface regardless of spine.
    """
    if event_type == "score_churn":
        return {"type": "score_churn", "customer_id": obs.get("customer_id")}
    if event_type == "draft_offer":
        return {"type": "draft_offer", "discount_pct": payload.get("discount_pct", 15)}
    if event_type == "publish_offer":
        return {"type": "publish_offer", "discount_pct": payload.get("discount_pct", 15)}
    if event_type == "request_human_review":
        return {"type": "request_human_review", "reason": payload.get("reason", "policy")}
    if event_type == "accept_renewal":
        return {"type": "accept_renewal"}
    if event_type == "expire_renewal":
        return {"type": "expire_renewal"}
    return {"type": "stop", "reason": f"unknown_event_type:{event_type}"}
