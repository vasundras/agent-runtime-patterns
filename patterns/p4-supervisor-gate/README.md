# P4 · Supervisor + Gate

> **Control · "Decide whether work advances or halts"**
> Talk slide 08 (left-hand pattern)

## What it is

Two complementary control mechanisms running side-by-side:

- **Supervision (Erlang/OTP one-for-one restart)**: a supervisor heartbeats its children; when a child dies, the supervisor restarts just that child with exponential backoff. The rest of the system keeps running.
- **Gate (policy check before every side-effect)**: every action goes through a policy gate that can `allow` or `deny → audit`. The LLM never gets to write to a system of record without passing the gate.

```
   SUPERVISION · one-for-one restart
                ┌────────────┐
                │ supervisor │
                │ heartbeat·backoff
                └─────┬──────┘
            ┌──────┬──┴──┬──────┐
            ▼      ▼     ▼      ▼
       child A·alive  child B·restart  child C·alive

   GATE · policy check before every side-effect
   caller → gate ──allow──→ side-effect
              │
              └──deny→audit
```

## When to reach for it

- You ship side-effects (writes to billing, CRM, email, anything users see).
- The cost of a wrong write is **higher** than the cost of slowing things down.
- You need a clean answer to "how do we cap blast radius?"

## When *not* to use it

- Pure-read pipelines (analytics, RAG retrieval) — no side-effects, no gate needed.
- Single-process scripts where supervision is just overhead.

## Failure modes

| Failure | Mitigation |
|---|---|
| Supervisor itself crashes | Run supervisor under a process manager (systemd, k8s, OTP root supervisor). |
| Gate becomes a bottleneck | Cache policy decisions; pre-compute per-tenant rules; fast deny path. |
| "Approved by AI" laundering | Gate decisions must log: who decided (policy version), why, what was denied. See [P6 HITL](../p6-human-in-the-loop/). |

## Files

- [`langgraph_example.py`](langgraph_example.py) — supervisor with heartbeat + restart, gate refusing an out-of-policy 90% discount.

## Reading list

See [P4 entries](../../papers/CURATED_BIBLIOGRAPHY.md#p4--supervisor--gate) — Armstrong (Erlang/OTP), NeMo Guardrails, GuardAgent, Constitutional AI, MAST.
