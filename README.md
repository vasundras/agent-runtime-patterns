# Runtime Architecture Patterns for Agents in Production

> *Reliability is not a model property. It is an engineering problem.*
> *Drift dominates variance.*

Companion repository to the AI Council 2026 talk **"Runtime Architecture Patterns for Agents in Production"** by [Vasundra Srinivasan](https://www.linkedin.com/in/vasundrasrinivasan/) — AI Architect Director (Salesforce), O'Reilly author of *Data Engineering for Multimodal AI*, independent researcher.

This repo packages the talk into five artifacts you can clone, read, and run:

1. **Six runnable patterns** — LangGraph by default, Google ADK where it fits better.
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
| **P1** | [Hierarchical Delegation](patterns/p1-hierarchical-delegation/) | Coordination | LangGraph + ADK | One owner of the work, N specialists, deterministic merge |
| **P2** | [Scatter-Gather + Saga](patterns/p2-scatter-gather-saga/) | Coordination | LangGraph | Parallel fan-out where some peers will fail and writes need undo |
| **P3** | [Event-Driven Sequencing](patterns/p3-event-driven-sequencing/) | State | LangGraph | The log is the source of truth; consumers are commentary |
| **P4** | [Supervisor + Gate](patterns/p4-supervisor-gate/) | Control | LangGraph | Restart what's dead, refuse what's out-of-policy, audit everything |
| **P5** | [Shared State Machine](patterns/p5-shared-state-machine/) | State | LangGraph | Long-horizon work that pauses, resumes, and tolerates restarts |
| **P6** | [Human in the Loop](patterns/p6-human-in-the-loop/) | Control | Google ADK | The four control planes: kill switch, escalation, approval, throttling |

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
