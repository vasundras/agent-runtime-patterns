# P5 · Shared State Machine

> **State · "Workers are stateless · pure (state, action) → next"**
> Talk slide 07 (right-hand pattern). The pattern the talk explicitly recommends investing in.

## What it is

A **durable, versioned state row** is the source of truth. Workers are stateless and pure: they read `(state, action)` and propose `next` via a **compare-and-swap (CAS)** against the version. The store rejects stale writes. Workers are commentary; the store is the system.

```
   ┌────┐    ┌────┐    ┌────────────┐    ┌────┐    ┌─────────┐
   │ A  │ →  │ B  │ →  │ C·current  │ →  │ D  │ →  │terminal │
   │v=1 │    │v=2 │    │   v=3      │    │    │    │         │
   └────┘    └────┘    └────────────┘    └────┘    └─────────┘

   worker          propose:                     durable store
   stateless·pure  from = C    ─────────→       versioned · timers
   (state,action)  to   = D                     CAS on (id, v)
   →next           ifVersion=3
```

## Why the talk recommends this over P3 (event-driven)

From slide 12: *"We tried events. It failed. We're building the state machine."* — and slide 15: *"State — Iterating. POC'd Event-Driven · failed. P5 in build."*

State machines beat pure event-driven for long-horizon agent work because:

- **Truth is a row, not a derived projection** → no replay drift across model versions.
- **Timers attach to the row** → "30 days from now, transition `offer_sent → expired`" is a property of the state, not a fragile cron.
- **Pauses are first-class** → `human_required` is a state, not a missing event.

## When *not* to use it

- The workflow truly has no states — it's a one-shot transform. Use a stateless function.
- You need an immutable audit-grade trail. Combine with P3 (the state machine emits transition events to the log).

## Failure modes

| Failure | Mitigation |
|---|---|
| Worker proposes a stale transition | CAS rejects; worker re-reads and retries. |
| Two workers race for the same transition | CAS guarantees one wins; loser handles defeat gracefully. |
| Timer fires after manual override | Timers carry the `from_version` they were scheduled at; if the row has moved on, the timer is no-op. |

## Files

- [`langgraph_example.py`](langgraph_example.py) — durable state row, two competing workers, CAS, timers, `human_required` state.

## Reading list

See [P5 entries](../../papers/CURATED_BIBLIOGRAPHY.md#p5--shared-state-machine) — Paxos, Raft, Spanner, van der Aalst (Petri nets / workflow theory), DSPy.
