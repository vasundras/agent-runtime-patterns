# Runtime Architecture Patterns for Agents in Production

> *Reliability is not a model property. It is an engineering problem.*
> *Drift dominates variance.*

Companion repository to the AI Council 2026 talk **"Runtime Architecture Patterns for Agents in Production"** by [Vasundra Srinivasan](https://www.linkedin.com/in/vasundrasrinivasan/) — AI Architect Director (Salesforce), O'Reilly author of *Data Engineering for Multimodal AI*, independent researcher.

This repo packages the talk into five artifacts you can clone, read, and run:

1. **Six runnable patterns** — [LangGraph](https://langchain-ai.github.io/langgraph/) by default, [Google ADK](https://google.github.io/adk-docs/) where it fits better.
2. **One end-to-end example** — the 90-day contract renewal from the talk, composed from the patterns.
3. **A curated, verified bibliography** — 30 papers grounding every pattern in either distributed-systems classics or recent agent-systems research. All arXiv IDs and DOIs verified.
4. **Public data** — the IBM Telco Customer Churn dataset (7,043 real customer records, plus a fixed 100-row subset), projected into the talk's renewal state machine by `data/load_telco.py`.
5. **An eval harness** — `evals/` ships a [τ-bench](https://arxiv.org/abs/2406.12045) adapter (Yao et al., [arXiv:2406.12045](https://arxiv.org/abs/2406.12045)) so the patterns can be evaluated against a published agent-runtime benchmark with `pass^k` consistency metrics.

---

## The framework in one paragraph

Production LLM agents come in three runtimes — **Conversational** (seconds), **Autonomous** (minutes), **Long-Horizon** (days). Every production runtime has to answer three questions simultaneously: **how does work split and combine** (Coordination), **how does the system remember** (State), and **who decides what runs and when to stop** (Control). Six patterns answer those three questions. You don't pick one — you build at the intersection. **State is the spine. Coordination wraps it. Control bounds it.**

```
                  ┌──────────────────────────────────────────────────────┐
                  │                                                      │
   Coordination   │   P1  Hierarchical Delegation                        │
                  │   P2  Scatter-Gather + Saga                          │
                  │                                                      │
   ───────────────┼──────────────────────────────────────────────────────┤
                  │                                                      │
   State          │   P3  Event-Driven Sequencing                        │
   (the spine)    │   P5  Shared State Machine                           │
                  │                                                      │
   ───────────────┼──────────────────────────────────────────────────────┤
                  │                                                      │
   Control        │   P4  Supervisor + Gate                              │
                  │   P6  Human in the Loop                              │
                  │                                                      │
                  └──────────────────────────────────────────────────────┘
```

---

## The six patterns

| # | Pattern | Dimension | Primary stack | When to reach for it |
|---|---------|-----------|---------------|----------------------|
| **P1** | [Hierarchical Delegation](patterns/p1-hierarchical-delegation/) | Coordination | [LangGraph](https://langchain-ai.github.io/langgraph/) + [Google ADK](https://google.github.io/adk-docs/) | One owner of the work, N specialists, deterministic merge |
| **P2** | [Scatter-Gather + Saga](patterns/p2-scatter-gather-saga/) | Coordination | [LangGraph](https://langchain-ai.github.io/langgraph/) | Parallel fan-out where some peers will fail and writes need undo |
| **P3** | [Event-Driven Sequencing](patterns/p3-event-driven-sequencing/) | State | [LangGraph](https://langchain-ai.github.io/langgraph/) | The log is the source of truth; consumers are commentary |
| **P4** | [Supervisor + Gate](patterns/p4-supervisor-gate/) | Control | [LangGraph](https://langchain-ai.github.io/langgraph/) | Restart what's dead, refuse what's out-of-policy, audit everything |
| **P5** | [Shared State Machine](patterns/p5-shared-state-machine/) | State | [LangGraph](https://langchain-ai.github.io/langgraph/) | Long-horizon work that pauses, resumes, and tolerates restarts |
| **P6** | [Human in the Loop](patterns/p6-human-in-the-loop/) | Control | [Google ADK](https://google.github.io/adk-docs/) | The four control planes: kill switch, escalation, approval, throttling |

Each pattern directory contains:

- `README.md` — what it is, when to use it, failure modes, the talk slide it maps to
- `langgraph_example.py` (or `adk_example.py`) — runnable, ~100–200 lines, comments where the pattern decisions live
- A "wired test" you can run with `python <file>` against a stub LLM (no API key needed by default)

---

## The example: contract renewal, 90-day window

[`examples/contract-renewal/`](examples/contract-renewal/) — the running example from the talk. Composes **P1 + P2** (orchestrator + scatter), wraps them around a **P5** state machine, gates side-effects with **P4**, and pauses for humans with **P6**. The README walks through which pattern is doing what at each timestep on the 90-day timeline.

---

## The bibliography

[`papers/CURATED_BIBLIOGRAPHY.md`](papers/CURATED_BIBLIOGRAPHY.md) — 30 papers, 5 per pattern, each verified by title + author + arXiv ID/DOI as of **2026-05-13**. Mix of:

- distributed-systems classics (Sagas, Paxos, Raft, Erlang/OTP, event sourcing, Petri nets)
- recent agent-systems papers (AutoGen, MetaGPT, HuggingGPT, CAMEL, AgentVerse, GuardAgent, NeMo Guardrails, MAST, DSPy, Reflexion, Constitutional AI, multi-agent debate)

If you find a broken link or a citation that doesn't resolve, file an issue.

---

## Prerequisites

New to these frameworks? Start here before cloning.

| What you need | Why | Where to get it |
|---------------|-----|-----------------|
| **Python 3.10+** | Required runtime | [python.org/downloads](https://www.python.org/downloads/) — run `python --version` to check |
| **[LangGraph](https://langchain-ai.github.io/langgraph/)** | Graph runtime powering P1–P5 | [Docs](https://langchain-ai.github.io/langgraph/) · [Quickstart](https://langchain-ai.github.io/langgraph/tutorials/introduction/) · [GitHub](https://github.com/langchain-ai/langgraph) |
| **[Google ADK](https://google.github.io/adk-docs/)** | Agent runtime for P1 + P6 variants | [Docs](https://google.github.io/adk-docs/) · [GitHub](https://github.com/google/adk-python) · [Quickstart](https://google.github.io/adk-docs/get-started/quickstart/) |
| **[LangChain](https://python.langchain.com/)** | Model connectors (Anthropic, OpenAI) | Installed automatically via `requirements.txt` |
| **API key** *(optional)* | Only needed for real LLM calls | [Anthropic Console](https://console.anthropic.com/) or [OpenAI Platform](https://platform.openai.com/) |

> All six patterns ship with a **stub LLM** — every example runs fully offline out of the box. You do not need an API key to explore the structure or swap in your own data.

---

## Quick start

```bash
git clone https://github.com/vasundras/agent-runtime-patterns
cd agent-runtime-patterns
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run any pattern standalone — they ship with a stub LLM and require no API key
python patterns/p1-hierarchical-delegation/langgraph_example.py
python patterns/p5-shared-state-machine/langgraph_example.py

# Run the full contract-renewal example
python examples/contract-renewal/run.py

# Project the IBM Telco corpus into renewal-shaped rows (real public data)
python data/load_telco.py

# Build τ-bench-style scenarios from the Telco subset and run a structural dry-run
python evals/scenarios_telco.py
python evals/run_eval.py --k 4 --limit 10
```

To wire a real LLM, export `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` and set `USE_REAL_LLM=1`. To run a live τ-bench eval, also `pip install git+https://github.com/sierra-research/tau-bench` and pass `--live`.

---

## Bring Your Own Dataset — lab guide

The telco renewal scenario is just the default skin. The patterns are domain-agnostic — swap three things and you're running your own data in under 15 minutes.

### Which pattern fits your problem?

| Your scenario | Pattern |
|--------------|---------|
| One coordinator, multiple specialist steps, deterministic merge | **[P1](patterns/p1-hierarchical-delegation/)** Hierarchical Delegation |
| Parallel checks where some may fail and you need compensating rollback | **[P2](patterns/p2-scatter-gather-saga/)** Scatter-Gather + Saga |
| Audit trail is critical; you need replay, branching, or time-travel debug | **[P3](patterns/p3-event-driven-sequencing/)** Event-Driven Sequencing |
| Agents crash in prod and side-effects need policy enforcement before they fire | **[P4](patterns/p4-supervisor-gate/)** Supervisor + Gate |
| Long-running job that pauses overnight, resumes, and tolerates restarts | **[P5](patterns/p5-shared-state-machine/)** Shared State Machine |
| Humans must be able to approve, escalate, kill, or throttle at runtime | **[P6](patterns/p6-human-in-the-loop/)** Human in the Loop |

### The three swap points (P1–P4)

Every LangGraph pattern (`langgraph_example.py`) has exactly three places to touch:

**1. The state `TypedDict` — rename fields to your domain**

```python
# Default (telco renewal)
class RenewalState(TypedDict, total=False):
    renewal_id: str
    customer:   dict[str, Any]
    churn:      dict[str, Any]   # sub-agent output
    offer:      dict[str, Any]   # sub-agent output
    decision:   dict[str, Any]   # merged result
    failures:   Annotated[list[str], operator.add]

# Your domain (e.g. medical triage)
class TriageState(TypedDict, total=False):
    case_id:    str
    patient:    dict[str, Any]
    risk:       dict[str, Any]   # sub-agent output
    treatment:  dict[str, Any]   # sub-agent output
    disposition: dict[str, Any]  # merged result
    failures:   Annotated[list[str], operator.add]
```

Rename the class and its fields. Graph wiring, parallel fan-out, and merge logic are structurally unchanged — only field names move.

**2. The sub-agent stubs — replace hardcoded returns with your logic**

```python
# Default stub — always returns the same canned dict
def sub_churn(state: RenewalState) -> RenewalState:
    return {"churn": {"score": 0.72, "drivers": ["plan_eol"]}}

# Your version — call a real LLM (needs USE_REAL_LLM=1 and an API key)
def sub_risk(state: TriageState) -> TriageState:
    from _common import get_llm
    llm = get_llm()
    result = llm.invoke(f"Assess urgency: {state['patient']}")
    return {"risk": {"level": result, "source": "llm"}}
```

**3. The `app.invoke({...})` call — feed your records**

```python
# Single record
result = app.invoke({"case_id": "C-001", "patient": {"age": 45, "condition": "..."}})

# Loop over a CSV
import csv
with open("my_data.csv") as f:
    for row in csv.DictReader(f):
        result = app.invoke({"case_id": row["id"], "patient": dict(row)})
        print(result.get("disposition"))

# Loop over a JSON file
import json
for record in json.load(open("my_data.json")):
    result = app.invoke({"case_id": record["id"], "patient": record})
```

### P5 — Shared State Machine: one extra step

P5 also has an `ALLOWED_TRANSITIONS` dict that encodes your workflow's valid state moves. Update it to match your domain's lifecycle:

```python
# Default (renewal lifecycle)
ALLOWED_TRANSITIONS = {
    "pending":        {"scoring"},
    "scoring":        {"offer_sent", "human_required"},
    "offer_sent":     {"closed", "human_required", "expired"},
    "human_required": {"offer_sent", "closed", "expired"},
}

# Your domain (e.g. order fulfilment)
ALLOWED_TRANSITIONS = {
    "received":   {"validated"},
    "validated":  {"picking", "on_hold"},
    "picking":    {"packed", "on_hold"},
    "packed":     {"shipped"},
    "shipped":    {"delivered", "returned"},
}
```

### P6 — Human in the Loop: configure the four control planes

P6's swap points are thresholds, not field names. In `adk_example.py`, find and adjust:

| Plane | Variable to change | Default |
|-------|-------------------|---------|
| Kill switch | `CancellationToken.revoked` — call `.revoke()` from your orchestration layer | manual |
| Escalation | `suspend(reason=...)` inside the agent body | on any exception |
| Approval | `APPROVAL_TIMEOUT_S` | `5` seconds |
| Throttling | `RATE_LIMIT` (calls/min) and `BUDGET_LIMIT` ($/day) | `3` / `1.0` |

### Wiring a real LLM

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # or OPENAI_API_KEY=sk-...
export USE_REAL_LLM=1
python patterns/p1-hierarchical-delegation/langgraph_example.py
```

`get_llm()` in [`patterns/_common.py`](patterns/_common.py) picks up the key automatically — Anthropic is tried first, then OpenAI. No other changes needed.

## Data and citations at a glance

- **Customer corpus**: IBM Telco Customer Churn (7,043 rows, CC0-equivalent license). See [`data/SOURCES.md`](data/SOURCES.md).
- **Eval target**: [τ-bench — Yao, Shinn, Razavi, Narasimhan (arXiv:2406.12045)](https://arxiv.org/abs/2406.12045), Apache 2.0. See [`evals/README.md`](evals/README.md).
- **Bibliography**: [`papers/CURATED_BIBLIOGRAPHY.md`](papers/CURATED_BIBLIOGRAPHY.md) — 30 papers verified 2026-05-13; see [`papers/VERIFICATION_REPORT.md`](papers/VERIFICATION_REPORT.md) for the audit table.

---

## What this repo is *not*

- **Not a framework.** LangGraph and ADK are tools; the patterns are the substrate. The same six patterns reappear in Temporal, Restate, Inngest, durable-objects, BPMN engines.
- **Not exhaustive.** Six patterns won't cover RAG indexing, eval pipelines, prompt-management, model-router selection. Those are upstream of the runtime.
- **Grounded in the current state of the field.** Two strong positions from the talk reflect where the evidence stands today: (a) *prefer contracts over multi-agent debate*; (b) *build the operations console before the agent*. The agent-systems space is evolving fast — these positions will be revisited as the field matures.

---

## License

MIT. See [LICENSE](LICENSE).

## Citing this work

If you use this repo in your own research or in a production system, please cite the talk and the companion arXiv preprint (in preparation; see [`arxiv/`](arxiv/)):

```
Srinivasan, V. (2026). Runtime Architecture Patterns for Agents in Production.
AI Council 2026, Day 2 (AI Engineering Track). Companion repository.
```
