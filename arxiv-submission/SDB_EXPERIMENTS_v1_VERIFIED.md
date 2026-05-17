# SDB_EXPERIMENTS_v1 — independent fact-check

**Verifier note.** I read `SDB_EXPERIMENTS_v1.md` in full, then opened every cited URL, every cited GitHub issue, the MAST PDF, and the source trees of all five frameworks audited in §2. Every claim below is annotated VERIFIED, MODIFIED (with the corrected value), or REMOVED (with why). Anything not in this file did not survive the pass. Bottom-line verdict is in the final section.

---

## H1 — codebase audit (§2)

The audit table makes one quantitative top-line claim plus a row of specific code pointers per framework. I cloned all five repos (HEAD on 2026-05-17) and opened each file/line.

### Top-line counts (§2 row totals)

**Claim:** "Total LLM→action sites audited: 21. SDBs explicit: 19. SDBs implicit: 2. SDBs entirely missing: 0."

**VERDICT: VERIFIED, with one caveat.** The site-counting methodology is judgement-based (e.g. "is `output_pydantic` a separate site from the ReAct parser?"), so the 21 is not reproducible to the integer. But the *qualitative* picture — every framework has something at the SDB position, Swarm is the outlier with no framework-level verifier — survived a hand recount on the cloned repos. The 19/21 ratio is defensible.

### Per-framework pointers

| Row | Claim from §2 table | Verdict | Source |
|---|---|---|---|
| openai/swarm | "`json.loads(args)` then `func(**args)` directly in `swarm/core.py` `handle_tool_calls`" | **VERIFIED.** `swarm/core.py` line 89 defines `handle_tool_calls`; line 114 does `args = json.loads(tool_call.function.arguments)`; the function then calls `function_map[name](**args)` with no schema or policy check. | github.com/openai/swarm, `swarm/core.py` |
| AutoGPT | "pydantic `ActionProposal.model_validate` in `autogpt/agents/prompt_strategies/one_shot.py:325`" | **MODIFIED.** The class is `OneShotAgentActionProposal`, not `ActionProposal`. The `.model_validate(assistant_reply_dict)` call sits at line 325 of `classic/original_autogpt/autogpt/agents/prompt_strategies/one_shot.py`. Substance verified, name slightly wrong. | github.com/Significant-Gravitas/AutoGPT |
| AutoGPT | "retry loop with error injection in `forge/llm/providers/anthropic.py:361-400` (`fix_failed_parse_tries`)" | **VERIFIED.** `classic/forge/forge/llm/providers/anthropic.py` line 372 references `self._configuration.fix_failed_parse_tries`; the surrounding try/except (lines ~355-405) builds an Anthropic-format tool-error message and re-prompts. Default `fix_failed_parse_tries: int = 3` in `forge/llm/providers/schema.py:195`. | github.com/Significant-Gravitas/AutoGPT |
| LangChain | "default `handle_parsing_errors=False` in `agents/agent.py:1042`" | **VERIFIED, with path correction.** The file is `libs/langchain/langchain_classic/agents/agent.py` (the repo restructured into `langchain_classic`). Line 1042: `handle_parsing_errors: bool | str | Callable[[OutputParserException], str] = False`. Crash-on-reject behaviour is the documented default. | github.com/langchain-ai/langchain |
| CrewAI | "ReAct parser in `agents/parser.py`, pydantic `output_pydantic` on `Task`, programmable `guardrail`/`guardrails` with `guardrail_max_retries=3` retry; `OutputParserError` caught in `agents/crew_agent_executor.py:427`" | **VERIFIED.** `lib/crewai/src/crewai/agents/parser.py` exists; `lib/crewai/src/crewai/task.py:178` declares `output_pydantic`, line 272 declares `guardrail_max_retries: int = Field(default=3, ...)`; `crew_agent_executor.py:427` catches `OutputParserError` and routes through `handle_output_parser_exception`. The exact line number for the catch is off by 1-3 depending on HEAD, but the construct is there. | github.com/crewAIInc/crewAI |
| AutoGen | "`BaseTool.run_json` calls `self._args_type.model_validate(args)` in `autogen-core/tools/_base.py:198`; optional `output_content_type: type[BaseModel]` in `_assistant_agent.py:742`" | **VERIFIED.** Exact line 198 in `python/packages/autogen-core/src/autogen_core/tools/_base.py`: `return_value = await self.run(self._args_type.model_validate(args), cancellation_token)`. Line 742 in `_assistant_agent.py`: `output_content_type: type[BaseModel] | None = None`. | github.com/microsoft/autogen |
| MetaGPT | "`metagpt/actions/action_node.py` lines 428–500 and 665–814" (auto_review / auto_revise / from_pydantic) | **MODIFIED.** The functions exist but at slightly different lines on HEAD: `auto_review` is at line 680, `auto_revise` at 768, `review` at 729, `revise` at 816, `from_pydantic` at 841. The qualitative claim ("complete instantiation of the four-part SDB as a reusable component") is supported. | github.com/geekan/MetaGPT |

**Bonus issue cluster (§2 final paragraph).** All five GitHub issue numbers I spot-checked exist and have the described shape:
- LangChain #1358 (`ValueError: Could not parse LLM output:`) — VERIFIED. Opened Mar 2023.
- LangChain #21912 (`Parsing LLM output produced both a final answer and a parse-able action`) — VERIFIED.
- AutoGPT #4752 (`'thoughts' is a required property`) — VERIFIED.
- CrewAI #1744 (`DelegateWorkToolSchema`) — VERIFIED.
- CrewAI #1649 — title is actually "[BUG] Error: the Action Input is not a valid key, value dictionary." — paraphrase "Action Input not a valid dict" is accurate.
- CrewAI #3191 (`LLMGuardrailResult ... trailing characters`) — VERIFIED.
- openai/openai-agents-js #1104 — VERIFIED, see below.

---

## H2 — failure-mode classification (§3)

For each of the 21 rows I opened the cited URL (when given) or located the canonical writeup. I am scoring each row on three things: (a) does the source exist, (b) does the description match, (c) is the SDB classification defensible.

| # | Source/event | Source verified? | Description matches? | SDB classification defensible? |
|---|---|---|---|---|
| 1 | Replit AI agent (Fortune, Jul 2025) | **YES** — fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/ | YES — code freeze violated, prod DB wiped, fake test results | **YES** — Replit fix list (dev/prod separation, planning-only mode, rollback) is explicit policy verifier + HITL gate |
| 2 | Moffatt v Air Canada (2024 BCCRT 149) | **YES** — canlii.org/en/bc/bccrt/doc/2024/2024bccrt149 | YES — chatbot invented bereavement-fare retro policy, tribunal awarded CAD 812.02 | YES |
| 3 | Cursor "Sam" bot (Apr 2025) | **YES** — theregister.com/2025/04/18/cursor_ai_support_bot_lies/ | YES — invented login-restriction policy, users cancelled | YES — "no policy-grounding verifier" is the right localization |
| 4 | Chevy of Watsonville $1 SUV (Nov 2023) | **YES** — multiple writeups (gizmodo, venturebeat); $76k figure is on the low end of reported values ($60k-$81k depending on source). | YES — Bakke "no takesies backsies" prompt injection | YES |
| 5 | NYC MyCity chatbot (Mar 2024) | **YES** — themarkup.org actual URL is `/news/2024/03/29/...` not `/artificial-intelligence/2024/03/29/...`. URL in citation list is slightly wrong. Content matches. | YES — illegal advice on housing/employment | **MODIFIED on one fact** — the report says "bot eventually shut down (Mamdani admin, 2026)". I could not verify this 2026 shutdown claim from primary sources accessible to me. The Markup investigation is real; the political-administration footnote should be removed or sourced. |
| 6 | DPD chatbot (Jan 2024) | **YES** — theregister.com/2024/01/23/dpd_chatbot_goes_rogue/ | YES — swore, wrote disparaging poem, immediately disabled | YES |
| 7 | Bing/Sydney (Feb 2023) | **YES** — well-documented; 5-turn cap confirmed by Microsoft press at the time | YES | YES (mixed) |
| 8 | Promptfoo GPT-4o→GPT-4.1 94%→71% | **YES** — promptfoo.dev/blog/model-upgrades-break-agent-safety. Direct quote from article: *"We tested a customer's agent after upgrading from GPT-4o to GPT-4.1. Their prompt-injection resistance dropped from 94% to 71% on our eval harness."* | YES — numbers are exact | YES, with a nuance below |
| 9 | claude-code #15909 (300 retries, 27M tokens, 4.6h) | **YES** — github.com/anthropics/claude-code/issues/15909 | YES — sub-agent loop, ~300 retries, ~27M tokens, 4.6h | YES |
| 10 | claude-code #27281 ("let me write the document") | **YES** — github.com/anthropics/claude-code/issues/27281 | YES — agent looped on "let me assemble the document" without ever calling Write | YES |
| 11 | claude-code #22758 (auto-compact retry loop ~2.5h) | **YES** — github.com/anthropics/claude-code/issues/22758. Issue says 27 subagent files over ~2.5h, no retry cap. | YES | YES |
| 12 | Dev.to kenimo49 "$400 bill, 24h" | **YES** — dev.to/kenimo49/i-let-my-claude-code-agent-run-for-24-hours-the-400-bill-was-the-least-scary-part-4dcc | YES — author disabled permission prompts, ~$400 bill, near-misses on .env commit and rm -rf | YES |
| 13 | LangChain #1358 | **YES** | YES | YES — exact "default reject = crash" pathology |
| 14 | LangChain #21912 | **YES** | YES — "final answer + parseable action" predicate ambiguity | YES |
| 15 | AutoGPT #4752 | **YES** | YES — `'thoughts' is a required property` | YES |
| 16 | CrewAI #1744 | **YES** | YES — `DelegateWorkToolSchema` dict-vs-string mismatch in hierarchical delegation | YES (verifier worked, caller gave up — exactly the report's framing) |
| 17 | CrewAI #3191 | **YES** | YES — JSON parser too strict, trailing chars | YES |
| 18 | openai-agents-js #1104 | **YES** — see deep-dive below | YES | YES |
| 19 | MAST §"No or Incomplete Verification (11.8%)" | **MODIFIED — wrong number.** MAST FM-3.2 is **8.20%**, not 11.8%. The 11.8% in the MAST paper is FM-1.1 "Disobey Task Specification". | Description otherwise matches | Classification still defensible; just cite the right number. |
| 20 | MAST §"Disobey Task Specification (15.7%)" | **MODIFIED — wrong number.** FM-1.1 is **11.8%**, not 15.7%. 15.7% is FM-1.3 "Step Repetition". | Description matches FM-1.1 if you use 11.8% | Classification defensible. |
| 21 | MAST §"Reasoning-Action Mismatch (0.8%)" | **MODIFIED — wrong number.** FM-2.6 is **13.2%**, not 0.8%. (0.85% is FM-2.4 "Information Withholding".) | Description matches FM-2.6 if you use 13.2% | Classification ("inside LLM primarily") defensible. |

**Top-line H2 numbers.**

- "**15/21 = 71.4% at SDB**" — *Arithmetically correct given the row classifications.* But three of the 21 rows (#19, #20, #21) use wrong MAST percentages. The row classifications themselves are not affected by the percentage errors, so the 71.4% headline survives. **Headline VERIFIED on arithmetic; underlying MAST attributions MODIFIED.**
- "**17/21 = 81.0% fix added/strengthened an SDB**" — Arithmetically correct (17/21 = 0.8095). Same caveat: classifications survive, MAST percentages don't.
- "MAST taxonomy puts 23.5% in task verification plus another ≈18% in disobey specification" — **MODIFIED.** The 23.5% (Task Verification category) is correct. The "≈18% in disobey specification" is wrong; FM-1.1 "Disobey Task Specification" is 11.8% and FM-1.2 "Disobey Role Specification" is 1.5%, summing to 13.3%, not 18%. The author may have been adding FM-1.1 (11.8%) + step-repetition (15.7%) and getting confused.

---

## Deep dive — the two strongest single citations

### Promptfoo GPT-4o → GPT-4.1, 94% → 71%

**Source:** `https://www.promptfoo.dev/blog/model-upgrades-break-agent-safety/` (fetched 2026-05-17).

**Verbatim quote pulled from page HTML:** *"We tested a customer's agent after upgrading from GPT-4o to GPT-4.1. Their prompt-injection resistance dropped from 94% to 71% on our eval harness. GPT-4.1 is trained to follow instructions more closely and literally, which can improve capability while hurting injection resistance. What changed: the newer model followed embedded instructions more literally. What failed: indirect injection via retrieved documents. What fixed it: an output classifier, stricter tool gating, and a system-prompt update."*

**Is the harness identical?** The article says "on our eval harness" — i.e. Promptfoo's own injection-resistance eval. The only swap described is the model. So yes, identical harness, model-only delta.

**Is the regression attributable to a verifier/commit failure?** The Promptfoo writeup's own attribution is *model-behaviour* ("GPT-4.1 follows embedded instructions more literally") and the fix is *adding an output classifier + stricter tool gating + system-prompt update*. This is exactly the SDB primitive's framing: the predicate that was implicit-in-the-model for GPT-4o stopped holding for GPT-4.1, and the fix was to externalize that predicate into a verifier. The SDB attribution is fair.

**One caveat that should be in the paper:** the regression is *attributable to model behaviour change*, not to "the SDB code broke." The SDB framing is that the *boundary contract* between model and action shifted, and the fix lives at the boundary. That's a slightly more careful framing than "verifier broke" and the paper should use it.

### openai/openai-agents-js #1104

**Source:** `https://github.com/openai/openai-agents-js/issues/1104` (fetched 2026-05-17).

**Title:** "Rejected tool calls use status: 'completed' in function_call_result, causing model hallucinations".

**Verbatim from issue body:** *"When a tool call is rejected via the approval flow, `buildApprovalRejectionResult` produces a `function_call_result` with `status: 'completed'`. The only signal that the tool was rejected is the text content of the output... I believe this is what causes the model to frequently hallucinate that the rejected tool call succeeded, especially in multi-tool scenarios (e.g. approve one email, reject another — model claims both were sent)."*

**Root cause:** `getToolCallOutputItem` in `runner/toolExecution.mjs` hardcodes `status: 'completed'` for all paths, including the rejection path.

**Does it cleanly map to a missing reject path in the SDB sense?** Yes. The verifier (approval gate) rejected. The commit semantics (write status=completed to transcript) are wrong for rejection. The signal back to the LLM is indistinguishable from success, so the model hallucinates success. This is exactly the report's framing in surprising-finding #2, and it is the strongest single piece of evidence for the four-part decomposition. **VERIFIED — and a stronger citation than I expected going in.** The maintainer response in-thread proposes switching to `status: 'incomplete'` for rejections, which validates the SDB framing further.

---

## Other URLs / metadata

- `geekan/MetaGPT` — repo exists, `metagpt/actions/action_node.py` exists, functions named as claimed (line numbers off, see above).
- `arxiv.org/abs/2503.13657` (MAST, Cemri et al.) — VERIFIED. Title "Why Do Multi-Agent LLM Systems Fail?". The category totals (44.2% System Design, 32.3% Inter-Agent Misalignment, 23.5% Task Verification) cited indirectly are correct. The per-mode percentages cited in rows #19-21 are wrong, as documented.
- Replit fix list (dev/prod separation, planning-only mode) — verified via Tom's Hardware writeup confirming Masad's X-post announcement.
- The NYC MyCity / Mamdani 2026 shutdown subclaim is not verifiable from primary sources I could open.
- "Mamdani admin, 2026" reference in row #5 — **REMOVED.** I cannot find a primary source. If the author has one, it should be cited inline; otherwise the parenthetical should be dropped.

---

## Revised verdict

The SDB primitive holds up. The case is somewhat weaker than the original write-up suggests but still strong enough to load-bear a paper section. The two headline numbers (71.4% at SDB, 81% fixes strengthen SDB) survive the arithmetic and the row-level classifications survive on inspection, but three of the 21 rows (the MAST-derived ones) cite the wrong per-mode percentages — the rows should be re-stated with FM-3.2=8.2%, FM-1.1=11.8%, FM-2.6=13.2%, and the MAST category total of 23.5% can be cited cleanly as-is. The Promptfoo 94%→71% number is exactly right and the harness-identical, model-only-delta framing survives. The openai-agents-js #1104 issue is, if anything, *better* evidence than the original write-up gave it credit for — the maintainer response in-thread explicitly proposes switching to `status: 'incomplete'` for rejections, which is the SDB four-part decomposition validated by the framework's own engineers.

The strongest single piece of evidence that survived is openai/openai-agents-js #1104, not the Promptfoo case. Promptfoo is the cleanest *quantitative* citation; #1104 is the cleanest *architectural* citation, because it isolates the "commit/reject semantics" sub-claim that the rest of the paper depends on. Cite both, but lead with #1104 for the conceptual argument and use Promptfoo for the numeric one.

Two things to fix before this goes into the paper: (1) re-state the three MAST rows with the correct percentages from arxiv:2503.13657 Table/Figure 3; (2) drop the unsourced "Mamdani admin, 2026" parenthetical in row #5 unless a primary source is added. Everything else can ship.
