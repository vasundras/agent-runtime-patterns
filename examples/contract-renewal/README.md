# Contract Renewal · 90-Day Window

The running example from the talk. Telecoms lose 10–20% of monthly revenue to inefficient contract management and forgotten auto-renewals; this system closes that gap.

## How the patterns compose

```
   day -90               day -60            day -47            day -30           day -7         day 0
   ─────●─────────────────●──────────────────●──────────────────●─────────────────●─────────────●→
   window opens       scoring           PRODUCT EOL          outreach        close or escalate  renewed
                                       (world changes mid-flight)                              restructured
                                                                                               churned
```

| Stage | Patterns used | Why |
|---|---|---|
| Trigger arrives (day −90) | **P5** (init row), **P4** (gate admits the trigger) | One renewal row, versioned. Gate refuses duplicate triggers. |
| Signals fan out (usage / network / billing / support) | **P1** + **P2** | Orchestrator dispatches signal-fetchers in parallel; saga rolls back if one writes to billing and another fails. |
| Score + strategy | **P5** | Pure worker, CAS transition `scoring → offer_sent`. |
| EOL event mid-flight (day −47) | **P3** + **P5** | The event log records the EOL fact; the state machine transitions the row accordingly. |
| Outreach (day −30) | **P1** + **P4** | Orchestrator dispatches the outreach; gate refuses any discount over 30%. |
| Pricing / close (day −7) | **P5** + **P6** | Some cases (contract mergers, > 50% discounts) suspend for human review. |
| Done (day 0) | **P5** terminal state | `renewed` / `restructured` / `churned`. |

## What this code does

[`run.py`](run.py) walks one renewal end-to-end with all six patterns engaged. It prints a tagged trace mirroring the diagram above so you can see which pattern fires when.

```bash
python run.py
```

Actual output of `python run.py` (captured 2026-05-13):

```
[       trigger] open window  renewal_id='r-8f3a'
[            p4] gate allow  action='open_window'
[            p5] cas → window_open  id='r-8f3a' v=1
[            p1] orchestrator dispatch  agents=['churn', 'offer', 'contract']
[            p1] sub:churn ok  score=0.72
[            p1] sub:offer ok  discount=90
[            p1] sub:contract ok (wrote CRM)  crm_id='crm-r-8f3a-0'
[            p2] scatter-gather complete  results=3 saga=False
[            p5] cas → scoring  id='r-8f3a' v=2
[            p3] event appended  type='product_eol' id='<uuid>'
[            p5] absorbed mid-flight event into row data
[            p4] gate DENY  reason='discount 90% > max 30%'
[            p5] cas → human_required  id='r-8f3a' v=3
[            p6] escalation — workflow paused  workflow_id='r-8f3a' reason='discount_out_of_policy'
[           end] paused for human review  id='r-8f3a'
[         audit] final store  state='human_required' v=3
[         audit] events  n=1
[         audit] suspended  n=1
```

Notice how all six patterns are exercised: P4 admits the trigger, P5 holds the row and CAS-transitions it, P1 dispatches the three sub-agents, P2 reports a clean scatter-gather (no failures so no saga rollback), P3 captures the mid-flight EOL event, and the gate (P4 again) denies the hallucinated 90% discount — which routes through P5 to `human_required` and triggers P6 escalation.

## What this code is *not*

It is **not** a complete production system. There's no real database, no real LLM call, no real Slack escalation. The point is to make the **pattern composition** legible — every line of code names which pattern it's executing.
