# P3 · Event-Driven Sequencing

> **State · "Events bet on history"**
> Talk slide 07 (left-hand pattern)

## What it is

An **append-only event log** is the source of truth. Workers subscribe, react, and emit new events. The log is replayable, branchable, and survives every worker restart. Consumers are commentary on the log; the log itself is the system.

```
   EVENT LOG · append-only
   ●──●──●──●──●──●──→
       event.x   event.z   event.w
                 ▲▲▲
        ┌───────┼┼┼───────┐
        ▼       ▼▼        ▼
   consumer1 consumer2 consumer3
   subs event.z   at-least-once   emits new events
```

## When to reach for it

- You need a **legal/compliance trail** — what happened, in what order, who saw what.
- Multiple downstream consumers need the same upstream signal without coupling.
- You want **branchable replay** — re-run history with a new policy and compare.

## When *not* to use it (talk slide 12: "We tried events. It failed.")

- Most agent workloads have **out-of-order events**, late arrivals, and replay drift: re-running the same events through an LLM produces different outputs across model versions. Pure event-driven systems become very hard to reason about.
- When the workflow has clear states and gates → use [P5 Shared State Machine](../p5-shared-state-machine/) instead. The talk's recommendation.

## Failure modes

| Failure | Mitigation |
|---|---|
| **Replay drift** (LLM outputs differ on re-play) | Pin model version per event; record `model_version` in each event; consider it part of the event identity. |
| Missed events | At-least-once delivery + **idempotency keys** on every consumer side-effect. |
| Late / out-of-order events | Watermarking; consumers must handle "event from 4h ago" without breaking. |

## Files

- [`langgraph_example.py`](langgraph_example.py) — append-only log with three consumers and an idempotency-key check.

## Reading list

See [P3 entries](../../papers/CURATED_BIBLIOGRAPHY.md#p3--event-driven-sequencing) — Kreps "The Log", Paxos, Raft, Spanner, Generative Agents.
