# Curated Bibliography

**Runtime Architecture Patterns for Agents in Production**
Companion bibliography for the AI Council 2026 talk by Vasundra Srinivasan.

Each entry below has been verified by cross-checking title, authors, and identifier (arXiv ID / DOI / proceedings URL) against the canonical source.

Last verified: **2026-05-13**

---

## P1 — Hierarchical Delegation

Orchestrator dispatches work to sub-agents and merges results. Classical orchestrator/worker pattern applied to LLM agents.

1. **[AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation Framework](https://arxiv.org/abs/2308.08155)**
   - Authors: Qingyun Wu, Gagan Bansal, Jieyu Zhang, et al.
   - Year: 2023
   - Venue: arXiv preprint (later COLM 2024)
   - arXiv: [2308.08155](https://arxiv.org/abs/2308.08155)
   - Why this maps: Canonical orchestrator-of-conversable-agents framework; the `GroupChatManager` is a literal hierarchical dispatcher that routes messages to specialized agents and merges replies.

2. **[MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework](https://arxiv.org/abs/2308.00352)**
   - Authors: Sirui Hong, Mingchen Zhuge, Jiaqi Chen, et al.
   - Year: 2023
   - Venue: arXiv preprint (ICLR 2024)
   - arXiv: [2308.00352](https://arxiv.org/abs/2308.00352)
   - Why this maps: Encodes Standard Operating Procedures as an assembly-line of role-specialized agents under a coordinating layer — a direct realization of orchestrator/worker on top of LLMs.

3. **[HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face](https://arxiv.org/abs/2303.17580)**
   - Authors: Yongliang Shen, Kaitao Song, Xu Tan, et al.
   - Year: 2023
   - Venue: NeurIPS 2023
   - arXiv: [2303.17580](https://arxiv.org/abs/2303.17580)
   - Why this maps: LLM as an explicit controller that plans, dispatches to specialist model endpoints, and aggregates results — a textbook hierarchical-delegation runtime.

4. **[CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society](https://arxiv.org/abs/2303.17760)**
   - Authors: Guohao Li, Hasan Abed Al Kader Hammoud, Hani Itani, et al.
   - Year: 2023
   - Venue: NeurIPS 2023
   - arXiv: [2303.17760](https://arxiv.org/abs/2303.17760)
   - Why this maps: Foundational role-playing pattern (task specifier + assistant + user) that grounds the user-proxy/worker dispatch decomposition used by most modern frameworks.

5. **[AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors](https://arxiv.org/abs/2308.10848)**
   - Authors: Weize Chen, Yusheng Su, Jingwei Zuo, et al.
   - Year: 2023
   - Venue: arXiv preprint (ICLR 2024)
   - arXiv: [2308.10848](https://arxiv.org/abs/2308.10848)
   - Why this maps: Four-stage pipeline (recruit experts → decide → execute → evaluate) is hierarchical delegation with a dynamic team-composition step.

---

## P2 — Scatter-Gather + Saga

Parallel fan-out with compensation log for failures. Saga pattern applied to agent workflows.

1. **[Sagas](https://doi.org/10.1145/38713.38742)**
   - Authors: Hector Garcia-Molina, Kenneth Salem
   - Year: 1987
   - Venue: ACM SIGMOD International Conference on Management of Data
   - DOI: [10.1145/38713.38742](https://doi.org/10.1145/38713.38742)
   - Why this maps: The foundational paper that defines a saga as a sequence of local transactions with compensating actions — the formal basis for treating multi-step agent workflows as recoverable distributed transactions.

2. **[Life Beyond Distributed Transactions: An Apostate's Opinion](https://doi.org/10.1145/3012426.3025012)**
   - Authors: Pat Helland
   - Year: 2007 (CIDR), reissued 2016 in ACM Queue
   - Venue: CIDR 2007 / ACM Queue Vol. 14 No. 5
   - DOI: [10.1145/3012426.3025012](https://doi.org/10.1145/3012426.3025012)
   - Why this maps: Argues that at scale you cannot rely on 2PC and must instead build idempotent, retryable, compensable workflow — exactly the model that turns scatter-gather agent calls into reliable systems.

3. **[Eventually Consistent](https://doi.org/10.1145/1435417.1435432)**
   - Authors: Werner Vogels
   - Year: 2009
   - Venue: Communications of the ACM, Vol. 52 No. 1
   - DOI: [10.1145/1435417.1435432](https://doi.org/10.1145/1435417.1435432)
   - Why this maps: Frames the consistency / availability / partition tradeoffs that make compensation (not coordination) the right primitive when many sub-agents act in parallel.

4. **[Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657)**
   - Authors: Mert Cemri, Melissa Z. Pan, Shuyi Yang, et al.
   - Year: 2025
   - Venue: arXiv preprint
   - arXiv: [2503.13657](https://arxiv.org/abs/2503.13657)
   - Why this maps: Empirical taxonomy (MAST) showing inter-agent misalignment and verification failures dominate multi-agent crashes — the failure modes that scatter-gather + saga is built to contain.

5. **[Improving Factuality and Reasoning in Language Models through Multiagent Debate](https://arxiv.org/abs/2305.14325)**
   - Authors: Yilun Du, Shuang Li, Antonio Torralba, Joshua B. Tenenbaum, Igor Mordatch
   - Year: 2023
   - Venue: ICML 2024
   - arXiv: [2305.14325](https://arxiv.org/abs/2305.14325)
   - Why this maps: Parallel fan-out to multiple debating instances followed by a gather/reconciliation step — a fan-out/fan-in topology that benefits directly from saga-style partial-result handling.

---

## P3 — Event-Driven Sequencing

Append-only event log as source of truth; consumers subscribe; replayable and branchable.

1. **[The Log: What Every Software Engineer Should Know About Real-Time Data's Unifying Abstraction](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying)**
   - Authors: Jay Kreps
   - Year: 2013
   - Venue: LinkedIn Engineering (expanded as O'Reilly *I Heart Logs*, 2014)
   - Why this maps: The definitive modern argument for the append-only log as a system-of-record substrate; directly grounds using an event log as the single source of truth for agent state.

2. **[The Part-Time Parliament](https://doi.org/10.1145/279227.279229)**
   - Authors: Leslie Lamport
   - Year: 1998
   - Venue: ACM Transactions on Computer Systems, Vol. 16 No. 2
   - DOI: [10.1145/279227.279229](https://doi.org/10.1145/279227.279229)
   - Why this maps: Paxos formalizes a replicated state machine over an ordered log — the theoretical floor under any replayable/branchable event-sourced agent runtime.

3. **[In Search of an Understandable Consensus Algorithm (Raft)](https://www.usenix.org/conference/atc14/technical-sessions/presentation/ongaro)**
   - Authors: Diego Ongaro, John Ousterhout
   - Year: 2014
   - Venue: USENIX ATC 2014 (Best Paper)
   - Why this maps: Practical, log-centric consensus algorithm that powers most modern durable-event stores (etcd, Consul, CockroachDB) — the engineering reference for an event log you can trust to drive agent decisions.

4. **[Spanner: Google's Globally Distributed Database](https://doi.org/10.1145/2491245)**
   - Authors: James C. Corbett, Jeffrey Dean, Michael Epstein, et al.
   - Year: 2013
   - Venue: ACM Transactions on Computer Systems, Vol. 31 No. 3 (OSDI 2012)
   - DOI: [10.1145/2491245](https://doi.org/10.1145/2491245)
   - Why this maps: Demonstrates externally consistent ordered commit logs at planet scale; the canonical reference for the kind of durable, time-ordered substrate that event-driven agent systems aspire to.

5. **[Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442)**
   - Authors: Joon Sung Park, Joseph C. O'Brien, Carrie J. Cai, et al.
   - Year: 2023
   - Venue: ACM UIST 2023
   - arXiv: [2304.03442](https://arxiv.org/abs/2304.03442)
   - Why this maps: Agents are driven by an append-only memory stream of observations + reflections; retrieval and reflection happen *from* the log, which is the event-sourcing pattern applied to agent cognition.

---

## P4 — Supervisor + Gate

Erlang/OTP-style supervision tree (one-for-one restart, heartbeat, backoff) plus a policy gate that checks every side-effect before it ships.

1. **[Making Reliable Distributed Systems in the Presence of Software Errors](https://erlang.org/download/armstrong_thesis_2003.pdf)**
   - Authors: Joe Armstrong
   - Year: 2003
   - Venue: PhD Thesis, Royal Institute of Technology (KTH), Stockholm
   - Why this maps: The seminal text on supervision trees, "let it crash," and one-for-one restart — the exact failure-isolation model that should govern a fleet of agents in production.

2. **[NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails](https://arxiv.org/abs/2310.10501)**
   - Authors: Traian Rebedea, Razvan Dinu, Makesh Sreedhar, Christopher Parisien, Jonathan Cohen
   - Year: 2023
   - Venue: EMNLP 2023 (System Demonstrations)
   - arXiv: [2310.10501](https://arxiv.org/abs/2310.10501)
   - Why this maps: An explicit programmable policy gate sitting in front of LLM side-effects — the canonical recent reference for the "every action gets checked" half of the pattern.

3. **[GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning](https://arxiv.org/abs/2406.09187)**
   - Authors: Zhen Xiang, Linzhi Zheng, Yanjie Li, et al.
   - Year: 2024
   - Venue: arXiv preprint
   - arXiv: [2406.09187](https://arxiv.org/abs/2406.09187)
   - Why this maps: A guard agent that compiles safety policies into executable checks and intercepts every action — explicit gate semantics layered over an agent fleet.

4. **[Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073)**
   - Authors: Yuntao Bai, Saurav Kadavath, Sandipan Kundu, et al.
   - Year: 2022
   - Venue: arXiv preprint (Anthropic)
   - arXiv: [2212.08073](https://arxiv.org/abs/2212.08073)
   - Why this maps: Grounds the idea of a written, principle-based policy that gates model output — the "what does the gate enforce" half of supervisor+gate.

5. **[Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657)**
   - Authors: Mert Cemri, Melissa Z. Pan, Shuyi Yang, et al.
   - Year: 2025
   - Venue: arXiv preprint
   - arXiv: [2503.13657](https://arxiv.org/abs/2503.13657)
   - Why this maps: Documents that ~50% of MAS failures are "task specification & verification" or "inter-agent" — i.e., precisely the failure modes that supervision-tree restart and pre-action gating are designed to absorb.

---

## P5 — Shared State Machine

Durable versioned state row with CAS/optimistic concurrency; workers are stateless and pure `(state, action) → next`.

1. **[The Part-Time Parliament](https://doi.org/10.1145/279227.279229)**
   - Authors: Leslie Lamport
   - Year: 1998
   - Venue: ACM Transactions on Computer Systems, Vol. 16 No. 2
   - DOI: [10.1145/279227.279229](https://doi.org/10.1145/279227.279229)
   - Why this maps: Paxos *is* the replicated state-machine approach — the theoretical foundation for "many stateless workers converge on one durable state via consensus."

2. **[In Search of an Understandable Consensus Algorithm (Raft)](https://www.usenix.org/conference/atc14/technical-sessions/presentation/ongaro)**
   - Authors: Diego Ongaro, John Ousterhout
   - Year: 2014
   - Venue: USENIX ATC 2014
   - Why this maps: The engineering-grade reference implementation of replicated state machines; provides the leader-election + log-match semantics that make CAS-on-a-state-row practical.

3. **[Spanner: Google's Globally Distributed Database](https://doi.org/10.1145/2491245)**
   - Authors: James C. Corbett, Jeffrey Dean, Michael Epstein, et al.
   - Year: 2013
   - Venue: ACM TOCS Vol. 31 No. 3 (OSDI 2012)
   - DOI: [10.1145/2491245](https://doi.org/10.1145/2491245)
   - Why this maps: Production-scale demonstration of versioned, externally-consistent rows with optimistic concurrency — the durable-state-row primitive lifted to a global system.

4. **[The Application of Petri Nets to Workflow Management](https://doi.org/10.1142/S0218126698000043)**
   - Authors: Wil M.P. van der Aalst
   - Year: 1998
   - Venue: Journal of Circuits, Systems and Computers, Vol. 8 No. 1
   - DOI: [10.1142/S0218126698000043](https://doi.org/10.1142/S0218126698000043)
   - Why this maps: Foundational formal model treating a workflow as a state machine over tokens/places; gives precise semantics to `(state, action) → next` transitions for long-running agent processes.

5. **[DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines](https://arxiv.org/abs/2310.03714)**
   - Authors: Omar Khattab, Arnav Singhvi, Paridhi Maheshwari, et al.
   - Year: 2023
   - Venue: ICLR 2024
   - arXiv: [2310.03714](https://arxiv.org/abs/2310.03714)
   - Why this maps: Compiles LM pipelines into declarative, deterministic modules with explicit signatures — pushes agent logic toward pure `(state, action) → next` functions a state machine can drive.

---

## P6 — Human in the Loop

Kill switch, escalation, approval workflow, throttling, durable suspend — the four control planes.

1. **[A Survey of Human-in-the-Loop for Machine Learning](https://arxiv.org/abs/2108.00941)**
   - Authors: Xingjiao Wu, Luwei Xiao, Yixuan Sun, et al.
   - Year: 2022
   - Venue: Future Generation Computer Systems (Elsevier), Vol. 135
   - arXiv: [2108.00941](https://arxiv.org/abs/2108.00941)
   - Why this maps: Comprehensive taxonomy of HITL designs (data, training-time, system-level intervention) — provides the conceptual backbone for the four control planes.

2. **[Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073)**
   - Authors: Yuntao Bai, Saurav Kadavath, Sandipan Kundu, et al.
   - Year: 2022
   - Venue: arXiv preprint (Anthropic)
   - arXiv: [2212.08073](https://arxiv.org/abs/2212.08073)
   - Why this maps: Defines a written, auditable rubric that humans curate and that the system enforces at inference — the policy backbone of an approval/escalation plane.

3. **[Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366)**
   - Authors: Noah Shinn, Federico Cassano, Edward Berman, et al.
   - Year: 2023
   - Venue: NeurIPS 2023
   - arXiv: [2303.11366](https://arxiv.org/abs/2303.11366)
   - Why this maps: Concrete pattern for an agent to *durably suspend* on a failure signal, capture a reflection (human- or signal-driven), and resume — the suspend/resume control plane in microcosm.

4. **[Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685)**
   - Authors: Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, et al.
   - Year: 2023
   - Venue: NeurIPS 2023 (Datasets & Benchmarks)
   - arXiv: [2306.05685](https://arxiv.org/abs/2306.05685)
   - Why this maps: Quantifies when LLM judgments agree with human judgments and where they diverge — the empirical guide for deciding which approvals can be delegated to a judge and which must escalate.

5. **[GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning](https://arxiv.org/abs/2406.09187)**
   - Authors: Zhen Xiang, Linzhi Zheng, Yanjie Li, et al.
   - Year: 2024
   - Venue: arXiv preprint
   - arXiv: [2406.09187](https://arxiv.org/abs/2406.09187)
   - Why this maps: Implements an interceptor that can block, throttle, or escalate every agent action against a policy — the kill-switch / throttling planes operationalized.

---

## Notes on Verification

All arXiv IDs above have been verified by direct lookup at `https://arxiv.org/abs/<id>`. DOI entries resolve via `https://doi.org/<DOI>`. When a paper had multiple versions (v1, v2, …), the citation refers to the canonical record identified by the bare arXiv ID.

If a future reader finds a broken link, the bare arXiv ID, DOI, or title+author combination should always resolve via Google Scholar or Semantic Scholar.
