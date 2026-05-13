# P2 · Scatter-Gather + Saga

> **Coordination · "Scatter · gather · aggregate" + compensation log**
> Talk slide 06 (right-hand pattern)

## What it is

Coordinator broadcasts a task to N **peer** workers in parallel, gathers responses, and aggregates. The twist is the **saga**: each worker logs a compensating action so that if peer B fails *after* peer C wrote to billing, we can `undo(billing.write)`.

```
                       ┌────────────┐
                       │coordinator │
                       │scatter→gather→aggregate
                       └─────┬──────┘
                ┌───────────┼───────────┐
                ▼           ▼           ▼
           ┌────────┐  ┌────────┐  ┌────────┐
           │ peer A │  │ peer B │  │ peer C │
           │  ok    │  │timeout │  │ ok, wrote external
           └────────┘  └────────┘  └────────┘
                              │
                              ▼
     SAGA · COMPENSATION LOG
     + peer C : action(...)  ← compensate: peer C : undo(...)
```

## When to reach for it

- Peers are symmetric (any one of them could be the "main" worker).
- Some of them have **side-effects** the system cannot easily roll back — payments, emails, external API calls.
- You'd rather pay the cost of a compensation log than risk inconsistent state.

## When *not* to use it

- All peer work is pure / idempotent → use [P1](../p1-hierarchical-delegation/) and skip the saga.
- You have access to a real distributed transaction manager → use it; sagas are a workaround for the absence of one.

## Failure modes

| Failure | Mitigation |
|---|---|
| Compensation itself fails | Compensations must be **idempotent**; log retries, then escalate to [P6 HITL](../p6-human-in-the-loop/). |
| Out-of-order compensation | Compensations run in **reverse order** of the original actions, even if the failure is mid-flight. |
| Compensation logic gets more complex than the original | Talk slide 11: "The saga. Compensation logic gets harder than the original logic." Sometimes the right answer is to make the original action two-phase instead. |

## Files

- [`langgraph_example.py`](langgraph_example.py) — three peers in parallel, one fails, the saga rolls back the others' external writes.

## Reading list

See [P2 entries](../../papers/CURATED_BIBLIOGRAPHY.md#p2--scatter-gather--saga) — Garcia-Molina & Salem (Sagas, SIGMOD 1987), Helland, Vogels, MAST, multi-agent debate.
