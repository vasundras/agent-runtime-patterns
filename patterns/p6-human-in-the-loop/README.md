# P6 · Human in the Loop

> **Control · "The four control planes"**
> Talk slide 08 (right-hand pattern)

## What it is

Four distinct control planes that sit between the agent and the rest of the system:

| Plane | What it does | SLA |
|---|---|---|
| **Kill switch** | `revoke cancellation_token` — stops the renewal in ~1s. No questions asked. | seconds |
| **Escalation** | Worker signals `suspend(reason)` — durable wait until a human decides. | minutes–days |
| **Approval** | Sync wait under SLA; on timeout → fallback policy. | minutes |
| **Throttling** | Blast-radius caps: N/min, $/day. Refuse work that would exceed. | continuous |

All four emit to a single audit trail.

## Why ADK fits this one

Google ADK separates `LlmAgent`, `SequentialAgent`, `ParallelAgent`, and (in beta) human-in-the-loop callbacks. The four control planes map cleanly onto ADK's lifecycle hooks: `before_agent_callback`, `before_tool_callback`, `after_tool_callback`, and `on_state_change`. The same pattern works in LangGraph with `interrupt_before` / `interrupt_after`, but ADK names the seams more directly.

## When to reach for it

- You ship work that, if wrong, has **legal**, **financial**, or **reputational** consequences.
- Some decisions are outside your envelope (the "merger of two contracts" example from slide 13).
- You need to be able to halt the agent **right now** in front of a regulator.

## When *not* to use it

- Low-stakes pure-read workflows.
- Anywhere a human is just rubber-stamping — that's not HITL, that's theater. The talk: *"Humans can be inconsistent too."*

## Files

- [`adk_example.py`](adk_example.py) — all four planes wired to a `worker_fleet` agent.
- [`langgraph_example.py`](langgraph_example.py) — the same four planes in LangGraph using `interrupt_before` and a checkpointer.

## Reading list

See [P6 entries](../../papers/CURATED_BIBLIOGRAPHY.md#p6--human-in-the-loop) — Wu et al. HITL survey, Constitutional AI, Reflexion, LLM-as-judge, GuardAgent.
