# P1 · Hierarchical Delegation

> **Coordination · "Orchestrator owns the work · dispatches"**
> Talk slide 06 (Concern 01 of 03 · Coordination)

## What it is

One **orchestrator** node owns the task. It dispatches sub-tasks to N **specialist sub-agents**, waits for their results, and merges. The orchestrator is the *only* component that touches the final output.

```
                ┌─────────────────────────┐
                │      orchestrator       │
                │   owns the work · merges│
                └────────┬────────────────┘
                  ┌──────┼──────┐
                  ▼      ▼      ▼
            ┌────────┐┌────────┐┌────────┐
            │ subA   ││ subB   ││ subC   │
            │step→r  ││step→r  ││step→r  │
            └────────┘└────────┘└────────┘
```

## When to reach for it

- One clear "owner" of an outcome exists (a renewal, a ticket, a draft).
- Sub-tasks are mostly independent but their *merge* is non-trivial (priorities, conflicts, schema reconciliation).
- You need a **single retry budget** at the orchestrator level rather than N independent ones.

## When *not* to use it

- Peers need to negotiate among themselves → consider [P2 Scatter-Gather + Saga](../p2-scatter-gather-saga/) or a contract pattern.
- The "merge" step is essentially `concat()` → you don't need a hierarchy; a stateless flat fan-out is cheaper.

## Failure modes

| Failure | Mitigation |
|---|---|
| One sub-agent stalls past deadline | Orchestrator enforces per-sub-agent timeout + partial-result policy (drop / substitute / fail-fast). |
| Sub-agents disagree on overlapping fields | Encode a deterministic merge priority in the orchestrator, never rely on the LLM to "decide". |
| Sub-agent retries shadow the orchestrator's retries | Disable retries on sub-agents; budget belongs to the parent. |
| Orchestrator becomes a god-prompt | Move sub-agent selection logic into typed routing (see "Don't do debate, do contracts" — talk slide 19). |

## Files

- [`langgraph_example.py`](langgraph_example.py) — orchestrator + 3 sub-agents, partial-result policy.
- [`adk_example.py`](adk_example.py) — same pattern using Google ADK's `SequentialAgent` / `ParallelAgent` composition, which makes the orchestrator/worker shape native.

## Reading list

See [P1 entries](../../papers/CURATED_BIBLIOGRAPHY.md#p1--hierarchical-delegation) — AutoGen, MetaGPT, HuggingGPT, CAMEL, AgentVerse.
