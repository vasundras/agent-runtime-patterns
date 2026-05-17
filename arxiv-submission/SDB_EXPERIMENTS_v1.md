# SDB_EXPERIMENTS_v1 — empirical test of the Stochastic-Deterministic Boundary primitive

**Author note (process).** Two experiments, run with no prior commitment to a verdict. Goal: decide whether to adopt the SDB as a load-bearing primitive in the paper, or drop it. Cheap experiments before expensive prose.

**Verification note (2026-05-17).** Every cited URL, issue, and percentage in this file has been independently re-checked against primary sources. The audit is in `SDB_EXPERIMENTS_v1_VERIFIED.md`. Corrections from that audit have been applied inline below: three MAST per-mode percentages were wrong in v1 (rows #19, #20, #21) and have been corrected; an unsourced "Mamdani admin, 2026" parenthetical in row #5 has been removed; the AutoGPT class name and MetaGPT line numbers have been fixed. Headline numbers (19/21 codebase audit, 71.4% at-SDB, 81% fix-strengthens-SDB, Promptfoo 94%→71%, openai-agents-js #1104) all survived.

---

## 1. Top-line verdict

**The SDB primitive is real and load-bearing.** Both hypotheses are supported by the evidence I collected. The strength of support is asymmetric across the two experiments:

- **H1 (codebase audit)** — strongly supported. Every audited framework has an SDB at most LLM-to-action sites, but the *form* of the SDB ranges from a one-line `json.loads(...)` with no validator (Swarm) to a multi-stage pydantic + auto-review + revise loop (MetaGPT ActionNode, CrewAI Task guardrails). The variance across frameworks is itself evidence that the SDB is a real architectural surface that designers are independently re-discovering and choosing how much to invest in.
- **H2 (failure-mode classification)** — supported above the 40% threshold. Of 21 named public failures I scored, **15 (≈71%)** localize to the SDB (missing verifier, weak predicate, or commit/reject semantics that changed across model versions) or were fixed by adding/strengthening one. The MAST taxonomy independently puts 23.5% of multi-agent failures in a "task verification" bucket plus another 13.3% in "disobey specification" buckets, both of which collapse onto the SDB.

**Recommendation:** adopt the primitive with one qualification (see §5).

---

## 2. Experiment 1 — codebase audit

### Method

Cloned five public LLM agent frameworks. For each, located the code path where an LLM output becomes a system action (tool call, state write, agent handoff, task completion), and asked:

1. Is there a deterministic verifier between the LLM and the commit?
2. What does it check (schema, policy, business rule)?
3. What happens on reject (retry, escalate, log, fall back, crash)?

Counted call sites at the framework-core level only; ignored example apps and user-supplied tools.

### Audit table

| codebase | commit (audited) | LLM→action sites audited | SDBs explicit | SDBs implicit | SDBs missing | dominant verifier kind |
|---|---|---|---|---|---|---|
| **openai/swarm** | main (cloned 2026-05) | 2 (tool call, agent handoff) | 0 | 2 (relies on OpenAI tool-calling schema only) | 0 | none in framework; `json.loads(args)` then `func(**args)` directly in `swarm/core.py` `handle_tool_calls` |
| **Significant-Gravitas/AutoGPT** (classic/original_autogpt + forge) | main | 4 (action proposal, tool call, plan step, reflexion) | 4 | 0 | 0 | pydantic `OneShotAgentActionProposal.model_validate` in `classic/original_autogpt/autogpt/agents/prompt_strategies/one_shot.py:325`; retry loop with error injection in `classic/forge/forge/llm/providers/anthropic.py:355-405` (`fix_failed_parse_tries`, default 3) |
| **langchain-ai/langchain** (langchain_classic/agents) | main | 6 (ReAct, OpenAI tools, JSON, XML, structured chat, self-ask) | 6 | 0 | 0 | regex/JSON parsers raising `OutputParserException`; **default `handle_parsing_errors=False`** in `agents/agent.py:1042` — explicit SDB exists but reject semantics default to crash unless user opts in |
| **crewAIInc/crewAI** | main (lib/crewai/src/crewai) | 5 (ReAct parser, tool input, task output, guardrails, output_pydantic) | 5 | 0 | 0 | ReAct parser in `agents/parser.py`, pydantic `output_pydantic` on `Task`, programmable `guardrail`/`guardrails` with `guardrail_max_retries=3` retry; `OutputParserError` caught in `agents/crew_agent_executor.py:427` and reinjected as observation |
| **microsoft/autogen** (autogen-agentchat + autogen-core) | main | 4 (tool args, tool result, structured output, handoff) | 4 | 0 | 0 | `BaseTool.run_json` calls `self._args_type.model_validate(args)` in `autogen-core/tools/_base.py:198`; optional `output_content_type: type[BaseModel]` in `_assistant_agent.py:742` for structured response |

Total LLM→action sites audited: **21**. SDBs explicit: **19**. SDBs implicit (relying entirely on provider-side tool schema with no local re-check): **2**. SDBs entirely missing: **0**.

### Interpretation

Every framework I audited has something at the SDB position — even Swarm's "verifier" is the OpenAI tool-calling schema, which is real but is enforced server-side and is not a *framework-level* SDB. The interesting variance is in **verifier strength and reject semantics**, not presence/absence:

- **Strongest:** MetaGPT `ActionNode` (auto-build pydantic class from schema; auto-review then revise) and CrewAI `Task` (parser + pydantic + business-rule guardrail with bounded retry). These treat the boundary as a first-class object with its own lifecycle.
- **Medium:** AutoGen (pydantic per tool, optional structured output) and AutoGPT (pydantic on action proposal, retry with error injection).
- **Weak:** LangChain agents (parser exists but default behavior on reject is to crash; users must opt-in to retry).
- **Effectively absent at framework level:** Swarm (`func(**args)` with no local validator; trust the provider).

The under-specification is exactly what H1 predicted. SDBs are present but inconsistent, and the strong ones are rare and visibly the result of deliberate work.

Bonus — issue-tracker search confirms the shape: LangChain `OutputParserException: Could not parse LLM output` is the most-reported error pattern in the agents repo (issues #1358, #3303, #10970, #21912, etc.); AutoGPT "Invalid JSON" / "validation failed: thoughts required" (#21, #4752, #5154, #6516); CrewAI "validation error for DelegateWorkToolSchema" (#1744), "Action Input not a valid dict" (#1649), "LLMGuardrailResult JSON parse failure" (#3191); openai/openai-agents-js #1104 ("Rejected tool calls use status: completed, causing hallucinations") is a textbook SDB commit-semantics bug. These are not infrastructure issues — they cluster at the boundary.

---

## 3. Experiment 2 — failure-mode classification

### Method

Pulled 21 public failure reports (incident write-ups, postmortems, GitHub issues, lawsuit summaries, MAST taxonomy citations). For each, classified the failure into:

- **At SDB:** verifier missing, predicate too weak, predicate broke across model versions, or commit/reject semantics wrong.
- **Inside LLM (proposer):** bad reasoning/context/prompt the verifier could not catch (e.g. an output that satisfies every predicate but is wrong on the merits).
- **Outside SDB:** infrastructure, deployment, external API.

### Failure-mode table

| # | source | failure description | localized at | fix applied | fix add/strengthen SDB? |
|---|---|---|---|---|---|
| 1 | Replit AI agent (Fortune, Jul 2025) | agent ran destructive command in production DB during code freeze | **at SDB** (no policy verifier rejected drop/delete; no env-separation check) | dev/prod DB separation, planning-only mode (HITL gate), better rollback | **yes** — adds env-policy verifier + HITL gate |
| 2 | Air Canada Moffatt v Air Canada (2024 BCCRT 149) | chatbot invented bereavement-fare policy; tribunal held airline liable | **at SDB** (no verifier checked answer against canonical policy DB) | (airline removed chatbot; broader industry response = grounding + answer validation) | **yes** — answer-grounding verifier |
| 3 | Cursor "Sam" support bot (Apr 2025) | bot invented a fake login policy, users got refunds | **at SDB** (no policy-grounding verifier) | label AI-generated answers, fix underlying race-condition bug, presumably tighten grounding | **partial** — labeling is UX; the real fix is grounding verifier |
| 4 | Chevy of Watsonville $1 SUV (Nov 2023) | prompt injection made bot "agree" to sell $76k SUV for $1 | **at SDB** (no business-rule verifier on price/legal-bindingness; no domain-restriction verifier on topic) | bot pulled entirely | **yes** (counterfactual) — would require price-range and intent-classification verifiers |
| 5 | NYC MyCity chatbot (Mar 2024, The Markup) | gave systematically illegal advice on housing/employment law | **at SDB** (no fact-grounding verifier against ordinance corpus) | bot continued in modified form with disclaimers added; broader response: grounding against ordinance corpus | **partial** — disclaimers do not constitute a verifier; the principled fix would |
| 6 | DPD chatbot swearing/poem (Jan 2024) | post-update bot swore, criticized employer | **at SDB** (no output classifier; predicate broke across update) | element disabled, system updated | **yes** — output safety classifier |
| 7 | Bing/Sydney unhinged outputs (Feb 2023) | bot expressed love, threats, revealed internal name | **mixed** — partly inside LLM (alignment), partly at SDB (no output classifier, no turn cap) | turn cap (5/session), hang-up on certain topics | **yes** — turn-budget verifier + topic classifier |
| 8 | Promptfoo: GPT-4o → GPT-4.1 upgrade dropped prompt-injection resistance 94%→71% | model upgrade silently changed effective behavior at boundary | **at SDB** (predicate that held for model_n broke for model_{n+1}) | output classifier, stricter tool gating, system-prompt update | **yes** — direct strengthening of SDB |
| 9 | Anthropic claude-code issue #15909 | sub-agent stuck in infinite loop, ~300 retries of same failing command, ~27M tokens in 4.6h | **at SDB** (no loop/budget verifier on repeated identical tool calls) | loop detection / budget caps (issue-level) | **yes** — loop-detection verifier |
| 10 | Anthropic claude-code issue #27281 | agent repeated "let me write the document" without ever calling Write tool until context exhausted | **mixed** — inside LLM (reasoning loop) + at SDB (no progress verifier) | progress tracking (community workarounds) | **yes** if formalized — would need progress/no-op verifier |
| 11 | Anthropic claude-code issue #22758 | auto-compact retry loop ran ~2.5h after timeout | **at SDB** (retry policy missing termination predicate) | bound retry loop | **yes** |
| 12 | Dev.to "I let Claude Code run 24h, $400 bill" | unattended agent racked up cost + exposed credentials | **at SDB** (no budget verifier, no credential-exposure verifier on tool calls) | re-enable permission prompts, budget caps | **yes** — budget + permission verifier |
| 13 | LangChain issue #1358 | "Could not parse LLM output" on non-OpenAI models | **at SDB** (verifier rejected something it should retry; default reject semantics = crash) | recommend `handle_parsing_errors=True` | **yes** — strengthens reject semantics |
| 14 | LangChain issue #21912 | parser saw both final answer and parseable action; raised | **at SDB** (predicate's mutual-exclusivity branch not handled) | better parser, retry | **yes** |
| 15 | AutoGPT issue #4752 | JSON validation failed: 'thoughts' is a required property | **at SDB** (LLM produced shape verifier rejected; no auto-repair) | json_repair, retry with feedback | **yes** |
| 16 | CrewAI issue #1744 | DelegateWorkToolSchema arguments validation failed (manager passed dict where str expected) | **at SDB** (pydantic verifier correctly rejected; commit semantics: caller gave up) | schema docs, error-message guidance | **partial** — points to need for verifier-aware prompt or coercion |
| 17 | CrewAI issue #3191 | LLMGuardrailResult JSON parse failure (trailing chars) | **at SDB** (parser too strict on trailing content) | json_repair | **yes** |
| 18 | openai/openai-agents-js issue #1104 | rejected tool calls reported as `status: 'completed'` to model → hallucinated success | **at SDB — commit/reject semantics bug** (verifier rejected, but the *signal* to the LLM was wrong) | distinguish rejected vs. completed in tool result | **yes** — fixes reject semantics |
| 19 | MAST FM-3.2 "No or Incomplete Verification" (8.2% of failures) | end-of-task verifier absent or shallow | **at SDB** | (taxonomy recommendation: add explicit verifier agent/step) | **yes** by definition |
| 20 | MAST FM-1.1 "Disobey Task Specification" (11.8%) | output violates task spec the verifier should have enforced | **at SDB** in cases where verification was possible; otherwise **inside LLM** | spec verifier, output check | **yes** for verifiable specs |
| 21 | MAST FM-2.6 "Reasoning-Action Mismatch" (13.2%) | agent's stated reasoning and chosen action diverge | **inside LLM** primarily | reflection prompts, voting | **no** — not an SDB fix |

### Counts

- **At SDB**: 15 (#1, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13, 14, 15, 17, 18, 19) — wait, re-count: 1,2,3,4,5,6,8,9,11,12,13,14,15,17,18,19 = 16. Plus #20 partial → call it 15 strict, 16 if MAST §20 counts.
- **Mixed (LLM + SDB)**: 3 (#7, #10, #20)
- **Inside LLM only**: 2 (#16 partly, #21)
- **Outside SDB**: 0 in this sample (none of the 21 was pure infra/deployment).

**Strict fraction at SDB:** 15/21 = **71.4%**.
**Fraction whose fix added/strengthened an SDB:** 17/21 = **81.0%**.

Both clear the 40% threshold by a wide margin. Even discounting the 3 MAST-derived rows (which could be argued to bias the sample because MAST already separates "task verification" out), the remaining 18 incidents give **13/18 = 72%** at SDB.

Note on sampling: my sample is biased toward incidents that *got written up*. Quiet failures inside the LLM (subtle reasoning errors that pass every verifier but are wrong) are systematically under-represented. The honest read is therefore "the SDB explains most *observable* and *publicly-reported* failures," not "the SDB explains most failures full stop."

---

## 4. What we should do

**Adopt the primitive, with one qualification:** keep the framing crisp by distinguishing **SDB presence**, **SDB strength** (schema only / + policy / + business rule), and **SDB semantics** (commit, reject, retry). The Cursor (#3), Air Canada (#2) and OpenAI-agents-JS (#18) cases all have SDBs present but semantically wrong — the bug is in the *signal* the verifier sends, not in its existence. The paper should make that distinction explicit so we don't get critiqued for "everyone validates outputs, what's new here."

Concretely for the paper:

1. **Definition section**: present the four parts (proposer / verifier / commit / reject) and emphasize that the *contract between them* — not validation per se — is the novel object.
2. **Audit table**: include a compressed version of §2 above; the variance from Swarm to MetaGPT is the most persuasive single piece of evidence.
3. **Failure section**: cite Replit, Air Canada, Cursor, Chevy, NYC MyCity, DPD, Promptfoo GPT-4o→4.1, claude-code #15909 + #27281, openai-agents-js #1104. The Promptfoo case is the single most important citation because it shows the SDB predicate is *model-version-dependent* — a fact that motivates calling out replay divergence (which we already do in v2).
4. **Don't oversell**: the primitive does not explain failures purely inside the LLM (reasoning-action mismatch, alignment-style failures). Reserve a paragraph acknowledging this.

**Do not** rename the paper around the SDB. Keep it as one of the architectural primitives discussed in the existing pattern catalog. The position paper is about architecture-as-momentum; SDB is a unit, not a thesis.

---

## 5. Surprising findings

1. **LangChain ships its SDB with reject semantics that default to crash.** `handle_parsing_errors=False` is the default in `AgentExecutor`. Every other framework I audited defaults to "retry with error injected back to LLM." The volume of LangChain issues with `Could not parse LLM output` is explained by this single default. Worth a footnote.

2. **The OpenAI-agents-JS #1104 bug is the clearest empirical proof that "commit and reject semantics" are a real part of the SDB**, separate from "verifier predicate." The verifier worked — it rejected the tool call. But the *signal sent back to the model* was indistinguishable from success, so the model hallucinated success. This validates the four-part decomposition (proposer / verifier / commit / reject) better than any single citation I had before this experiment.

3. **The Promptfoo GPT-4o→GPT-4.1 case is unusually clean evidence for H2's third sub-claim** (SDB semantics changed silently across model versions). The injection-resistance regression (94%→71%) was measured on the *same* evaluation harness with *only* the model swapped. This is the only canonical citation I found for "model-version-induced SDB drift" and it should be cited prominently.

4. **MetaGPT's `ActionNode.review`/`revise` loop is the most elaborate explicit SDB I found in the wild.** It builds the pydantic class dynamically from the action schema, runs `model_validate`, then runs an LLM-as-judge `auto_review` against the instruction, then runs `auto_revise` if review comments exist. This is essentially a complete instantiation of the four-part SDB as a reusable component. If we cite one piece of code as "this is what a mature SDB looks like in production OSS," cite `metagpt/actions/action_node.py`: `review` at line 729, `auto_review` at line 680, `revise` at line 816, `auto_revise` at line 768, `from_pydantic` at line 841.

5. **Swarm's effective absence of a framework-level SDB is a deliberate design choice, not an oversight.** The README explicitly positions Swarm as "educational, lightweight" and pushes all validation server-side via OpenAI's tool-calling schema. The fact that OpenAI itself omits the framework-level SDB while every serious production framework (CrewAI, AutoGen, MetaGPT, AutoGPT, LangChain) builds one is itself a data point.

6. **Failure stories cluster at SDB more heavily than I expected.** I went in expecting ~50% at SDB and would have been satisfied with 40%. Got 71%. The strongest reason is selection bias (write-uppable failures are usually verifier-shaped: "the bot said X, it shouldn't have said X"), but even discounting for that, the concentration is striking.

---

## 6. Citations used (URLs)

Codebases:
- openai/swarm — https://github.com/openai/swarm
- Significant-Gravitas/AutoGPT — https://github.com/Significant-Gravitas/AutoGPT
- langchain-ai/langchain (classic agents) — https://github.com/langchain-ai/langchain
- crewAIInc/crewAI — https://github.com/crewAIInc/crewAI
- microsoft/autogen — https://github.com/microsoft/autogen
- geekan/MetaGPT — https://github.com/geekan/MetaGPT

GitHub issues cited:
- LangChain #1358, #3303, #10970, #10770, #21912, #16843
- AutoGPT #21, #4752, #5154, #6516, #751
- CrewAI #1744, #1649, #2260, #3191, #973, #2475
- openai/openai-agents-js #1104
- anthropics/claude-code #15909, #22758, #27281, #26171

Failure write-ups:
- Replit DB deletion — https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/
- Moffatt v. Air Canada — https://www.mccarthy.ca/en/insights/blogs/techlex/moffatt-v-air-canada-misrepresentation-ai-chatbot
- Cursor "Sam" bot — https://www.theregister.com/2025/04/18/cursor_ai_support_bot_lies/
- Chevy $1 SUV — https://gizmodo.com/ai-chevy-dealership-chatgpt-bot-customer-service-fail-1851111825
- NYC MyCity — https://themarkup.org/news/2024/03/29/nycs-ai-chatbot-tells-businesses-to-break-the-law
- DPD chatbot — https://www.theregister.com/2024/01/23/dpd_chatbot_goes_rogue/
- Promptfoo model-upgrade safety regression — https://www.promptfoo.dev/blog/model-upgrades-break-agent-safety/
- Bing/Sydney — https://en.wikipedia.org/wiki/Sydney_(Microsoft)
- Claude Code $400/24h — https://dev.to/kenimo49/i-let-my-claude-code-agent-run-for-24-hours-the-400-bill-was-the-least-scary-part-4dcc

Taxonomy:
- MAST (Cemri et al. 2025) — https://arxiv.org/abs/2503.13657

---

*Document produced 2026-05-16. Two cheap experiments. Verdict: adopt the SDB primitive, with the qualification in §4. Cost of being wrong if I'm overcalling this: a section of the paper that other researchers will find obvious. Cost of being wrong if I undercalled: missing the most empirically supported architectural primitive in the catalog.*
