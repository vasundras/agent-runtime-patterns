# Verification Report — CURATED_BIBLIOGRAPHY.md

**Date:** 2026-05-13
**Verifier:** Independent re-check (not relying on prior "verified" markers in the source file).
**Method:** Each arXiv ID fetched at `https://arxiv.org/abs/<id>` and metadata (`citation_title`, `citation_author`, `citation_date`) extracted from the page. Non-arXiv entries verified via Google Scholar / publisher canonical URL / DOI resolver.

## Top-line summary

**30 of 30 verified, 0 partial, 0 broken.**

No fixes required in `CURATED_BIBLIOGRAPHY.md`.

---

## Full verification table

| Pattern | # | Title (truncated) | arXiv ID / venue | Status |
|---|---|---|---|---|
| P1 | 1 | AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation | arXiv:2308.08155 | VERIFIED |
| P1 | 2 | MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework | arXiv:2308.00352 | VERIFIED |
| P1 | 3 | HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face | arXiv:2303.17580 | VERIFIED |
| P1 | 4 | CAMEL: Communicative Agents for "Mind" Exploration of LLM Society | arXiv:2303.17760 | VERIFIED |
| P1 | 5 | AgentVerse: Facilitating Multi-Agent Collaboration and Emergent Behaviors | arXiv:2308.10848 | VERIFIED |
| P2 | 1 | Sagas | SIGMOD 1987, DOI 10.1145/38713.38742 | VERIFIED |
| P2 | 2 | Life Beyond Distributed Transactions: An Apostate's Opinion | ACM Queue 14(5) 2016, DOI 10.1145/3012426.3025012 | VERIFIED |
| P2 | 3 | Eventually Consistent | CACM 52(1) 2009, DOI 10.1145/1435417.1435432 | VERIFIED |
| P2 | 4 | Why Do Multi-Agent LLM Systems Fail? | arXiv:2503.13657 | VERIFIED |
| P2 | 5 | Improving Factuality and Reasoning through Multiagent Debate | arXiv:2305.14325 | VERIFIED |
| P3 | 1 | The Log: What Every Software Engineer Should Know... | LinkedIn Engineering (2013) | VERIFIED (URL resolves 200) |
| P3 | 2 | The Part-Time Parliament | ACM TOCS 16(2) 1998, DOI 10.1145/279227.279229 | VERIFIED |
| P3 | 3 | In Search of an Understandable Consensus Algorithm (Raft) | USENIX ATC 2014 | VERIFIED |
| P3 | 4 | Spanner: Google's Globally Distributed Database | ACM TOCS 31(3) 2013, DOI 10.1145/2491245 | VERIFIED |
| P3 | 5 | Generative Agents: Interactive Simulacra of Human Behavior | arXiv:2304.03442 | VERIFIED |
| P4 | 1 | Making Reliable Distributed Systems in the Presence of Software Errors | Armstrong PhD thesis, KTH 2003 | VERIFIED (URL resolves 200) |
| P4 | 2 | NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications | arXiv:2310.10501 | VERIFIED |
| P4 | 3 | GuardAgent: Safeguard LLM Agents by a Guard Agent | arXiv:2406.09187 | VERIFIED |
| P4 | 4 | Constitutional AI: Harmlessness from AI Feedback | arXiv:2212.08073 | VERIFIED |
| P4 | 5 | Why Do Multi-Agent LLM Systems Fail? | arXiv:2503.13657 | VERIFIED |
| P5 | 1 | The Part-Time Parliament | ACM TOCS 16(2) 1998, DOI 10.1145/279227.279229 | VERIFIED |
| P5 | 2 | In Search of an Understandable Consensus Algorithm (Raft) | USENIX ATC 2014 | VERIFIED |
| P5 | 3 | Spanner: Google's Globally Distributed Database | ACM TOCS 31(3) 2013, DOI 10.1145/2491245 | VERIFIED |
| P5 | 4 | The Application of Petri Nets to Workflow Management | J. Circuits Systems Computers 8(1) 1998, DOI 10.1142/S0218126698000043 | VERIFIED |
| P5 | 5 | DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines | arXiv:2310.03714 | VERIFIED |
| P6 | 1 | A Survey of Human-in-the-Loop for Machine Learning | arXiv:2108.00941 | VERIFIED (arXiv has lowercase "loop"; treated as minor punctuation) |
| P6 | 2 | Constitutional AI: Harmlessness from AI Feedback | arXiv:2212.08073 | VERIFIED |
| P6 | 3 | Reflexion: Language Agents with Verbal Reinforcement Learning | arXiv:2303.11366 | VERIFIED |
| P6 | 4 | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | arXiv:2306.05685 | VERIFIED |
| P6 | 5 | GuardAgent: Safeguard LLM Agents by a Guard Agent | arXiv:2406.09187 | VERIFIED |

---

## Per-citation evidence

For each arXiv ID, the canonical `citation_title`, first `citation_author`, and `citation_date` from the arXiv abstract page were compared to the bibliography entry.

| arXiv ID | arXiv title (canonical) | arXiv 1st author | arXiv submission year | Bib title match? | Bib author match? | Year ±1? |
|---|---|---|---|---|---|---|
| 2308.08155 | AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation | Wu, Qingyun | 2023 | yes | yes (Qingyun Wu) | yes (2023) |
| 2308.00352 | MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework | Hong, Sirui | 2023 | yes | yes (Sirui Hong) | yes (2023) |
| 2303.17580 | HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face | Shen, Yongliang | 2023 | yes | yes (Yongliang Shen) | yes (2023) |
| 2303.17760 | CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society | Li, Guohao | 2023 | yes | yes (Guohao Li) | yes (2023) |
| 2308.10848 | AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors | Chen, Weize | 2023 | yes | yes (Weize Chen) | yes (2023) |
| 2503.13657 | Why Do Multi-Agent LLM Systems Fail? | Cemri, Mert | 2025 | yes | yes (Mert Cemri) | yes (2025) |
| 2305.14325 | Improving Factuality and Reasoning in Language Models through Multiagent Debate | Du, Yilun | 2023 | yes | yes (Yilun Du) | yes (2023) |
| 2304.03442 | Generative Agents: Interactive Simulacra of Human Behavior | Park, Joon Sung | 2023 | yes | yes (Joon Sung Park) | yes (2023) |
| 2310.10501 | NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails | Rebedea, Traian | 2023 | yes | yes (Traian Rebedea) | yes (2023) |
| 2406.09187 | GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning | Xiang, Zhen | 2024 | yes | yes (Zhen Xiang) | yes (2024) |
| 2212.08073 | Constitutional AI: Harmlessness from AI Feedback | Bai, Yuntao | 2022 | yes | yes (Yuntao Bai) | yes (2022) |
| 2310.03714 | DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines | Khattab, Omar | 2023 | yes | yes (Omar Khattab) | yes (2023) |
| 2108.00941 | A Survey of Human-in-the-loop for Machine Learning | Wu, Xingjiao | 2021 | yes (minor: bib title capitalizes "Loop") | yes (Xingjiao Wu) | yes (2022 venue / 2021 arXiv, within ±1) |
| 2303.11366 | Reflexion: Language Agents with Verbal Reinforcement Learning | Shinn, Noah | 2023 | yes | yes (Noah Shinn) | yes (2023) |
| 2306.05685 | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | Zheng, Lianmin | 2023 | yes | yes (Lianmin Zheng) | yes (2023) |

For non-arXiv citations, the canonical record was located via Google Scholar / publisher DOI page and matched against the bibliography:

- **Sagas** — Garcia-Molina & Salem, SIGMOD 1987, DOI 10.1145/38713.38742 confirmed on ACM Digital Library and DBLP. Match.
- **Life Beyond Distributed Transactions: An Apostate's Opinion** — Pat Helland, ACM Queue Vol 14 No 5 (2016), DOI 10.1145/3012426.3025012 confirmed on ACM DL. Bibliography correctly notes "2007 (CIDR), reissued 2016 in ACM Queue"; the DOI points to the 2016 reissue. Match.
- **Eventually Consistent** — Werner Vogels, CACM 52(1) 2009, DOI 10.1145/1435417.1435432 confirmed on ACM DL and CACM page. Match.
- **The Part-Time Parliament** — Lamport, ACM TOCS 16(2) 1998, DOI 10.1145/279227.279229 confirmed on ACM DL. Match.
- **In Search of an Understandable Consensus Algorithm (Raft)** — Ongaro & Ousterhout, USENIX ATC 2014 (Best Paper Award), USENIX URL resolves 200. Match.
- **Spanner: Google's Globally Distributed Database** — Corbett et al., ACM TOCS 31(3) August 2013, DOI 10.1145/2491245 confirmed on ACM DL. Bibliography note "(OSDI 2012)" is the conference origin; TOCS 2013 is the journal version. Match.
- **The Application of Petri Nets to Workflow Management** — van der Aalst, JCSC 8(1) 1998, DOI 10.1142/S0218126698000043 confirmed on World Scientific. Match.
- **Making Reliable Distributed Systems in the Presence of Software Errors** — Armstrong, KTH 2003. The PDF URL `https://erlang.org/download/armstrong_thesis_2003.pdf` resolves with HTTP 200. Match.
- **The Log: What Every Software Engineer Should Know...** — Jay Kreps, LinkedIn Engineering 2013. The URL resolves with HTTP 200. Match.

---

## Notes

1. The duplicate citations of Lamport/Raft/Spanner (across P3 and P5) and of Constitutional AI / GuardAgent / Why Do Multi-Agent LLM Systems Fail? (across multiple patterns) are intentional cross-pattern references and not errors.
2. Minor cosmetic differences (e.g., capitalization of "Loop" vs. "loop" in the HITL survey title, "A Multi-Agent" vs. "a Multi-Agent" in MetaGPT) are treated as VERIFIED per the spec ("allow minor punctuation differences").
3. No BROKEN or PARTIAL citations were found, so no edits to `CURATED_BIBLIOGRAPHY.md` were needed.
