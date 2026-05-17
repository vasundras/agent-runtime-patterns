"""Anthropic SDK wrapper for the τ-bench spine ablation.

Wraps `anthropic` with three things the ablation needs:
  1. Model passthrough — switch between `claude-sonnet-4-5` and `claude-sonnet-4-6`
     so the §7 Δpass^k decomposes cleanly into model-version effects.
  2. Bounded retry — exponential backoff on 5xx and 429. Three attempts max.
     If retries are exhausted the call returns an error envelope that the spine
     can record as a non-fatal trial failure, not a harness crash.
  3. JSON-mode parsing — both spines need the model to emit a single JSON object
     (a proposed transition for P5, a proposed event for P3). We parse it here
     and surface a typed dict, not a raw string.

Every call writes one line to `evals/results/cost_ledger.jsonl` with input/output
tokens, latency, model, spine, and computed cost in USD. This is how the §7
cost-of-eval footnote gets its numbers.

Pricing (May 2026, list price per million tokens):
  - claude-sonnet-4-5: $3 in / $15 out
  - claude-sonnet-4-6: $3 in / $15 out
If pricing changes, edit `PRICE_PER_MTOK` below.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "patterns"))
from _common import log  # noqa: E402


PRICE_PER_MTOK = {
    "claude-sonnet-4-5": {"in": 3.00, "out": 15.00},
    "claude-sonnet-4-6": {"in": 3.00, "out": 15.00},
    # Dated revisions resolve back to the same pricing.
    "claude-sonnet-4-5-20251022": {"in": 3.00, "out": 15.00},
    "claude-sonnet-4-6-20260101": {"in": 3.00, "out": 15.00},
}


@dataclass
class CallResult:
    parsed: dict[str, Any]
    raw_text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    model: str
    error: str | None = None


@dataclass
class CostLedger:
    path: Path
    rows: list[dict[str, Any]] = field(default_factory=list)

    def record(self, *, spine: str, model: str, input_tokens: int,
               output_tokens: int, latency_ms: int, scenario_id: str,
               trial: int, error: str | None) -> None:
        price = PRICE_PER_MTOK.get(model, {"in": 3.00, "out": 15.00})
        cost = (input_tokens / 1_000_000) * price["in"] + (output_tokens / 1_000_000) * price["out"]
        row = {
            "ts": time.time(),
            "spine": spine,
            "model": model,
            "scenario_id": scenario_id,
            "trial": trial,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "cost_usd": round(cost, 6),
            "error": error,
        }
        self.rows.append(row)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as fh:
            fh.write(json.dumps(row) + "\n")


class LLMClient:
    """Thin wrap of anthropic.Anthropic with retry + JSON parsing + ledger.

    Lazily imports `anthropic` so the rest of the repo still runs in CI without it.
    """

    def __init__(self, model: str, *, spine: str, ledger: CostLedger,
                 max_retries: int = 3, base_delay: float = 1.5,
                 max_output_tokens: int = 512):
        self.model = model
        self.spine = spine
        self.ledger = ledger
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_output_tokens = max_output_tokens
        self._client = None  # lazy

    def _anthropic(self):
        if self._client is not None:
            return self._client
        try:
            import anthropic  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "anthropic SDK required for --live runs. "
                "`pip install anthropic>=0.39` and `export ANTHROPIC_API_KEY=...`"
            ) from e
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY not set in environment")
        self._client = anthropic.Anthropic()
        return self._client

    def propose(self, *, system: str, user: str, scenario_id: str, trial: int) -> CallResult:
        """One LLM round-trip. Returns parsed JSON or an error envelope.

        The spine is responsible for crafting `system` and `user` such that the
        model returns a single JSON object on a line. We grep the first `{...}`
        block out of the response.
        """
        client = self._anthropic()
        last_err: Exception | None = None
        t_start = time.time()

        for attempt in range(self.max_retries):
            try:
                resp = client.messages.create(
                    model=self.model,
                    max_tokens=self.max_output_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                latency_ms = int((time.time() - t_start) * 1000)
                raw = resp.content[0].text if resp.content else ""
                parsed = _extract_json_object(raw)
                in_tok = resp.usage.input_tokens
                out_tok = resp.usage.output_tokens
                self.ledger.record(
                    spine=self.spine, model=self.model,
                    input_tokens=in_tok, output_tokens=out_tok,
                    latency_ms=latency_ms, scenario_id=scenario_id, trial=trial,
                    error=None,
                )
                return CallResult(
                    parsed=parsed, raw_text=raw,
                    input_tokens=in_tok, output_tokens=out_tok,
                    latency_ms=latency_ms, model=self.model,
                )
            except Exception as e:  # noqa: BLE001 — broad catch is intentional
                last_err = e
                # 429/5xx → backoff; other errors → fail fast
                code = getattr(e, "status_code", None)
                if code in {429, 500, 502, 503, 504} and attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    log("llm", f"retry attempt={attempt + 1} after {delay:.1f}s", code=code, err=str(e))
                    time.sleep(delay)
                    continue
                break

        latency_ms = int((time.time() - t_start) * 1000)
        self.ledger.record(
            spine=self.spine, model=self.model,
            input_tokens=0, output_tokens=0,
            latency_ms=latency_ms, scenario_id=scenario_id, trial=trial,
            error=str(last_err) if last_err else "unknown",
        )
        return CallResult(
            parsed={"type": "stop", "reason": f"llm_error: {last_err}"},
            raw_text="",
            input_tokens=0, output_tokens=0, latency_ms=latency_ms,
            model=self.model, error=str(last_err) if last_err else "unknown",
        )


def _extract_json_object(text: str) -> dict[str, Any]:
    """Pull the first balanced {...} block out of a string.

    Models sometimes wrap JSON in code fences or add a prose preamble. We tolerate
    both. If extraction fails we return `{"type": "stop", "reason": "parse_error"}`
    so the trial terminates cleanly rather than crashing the harness.
    """
    if not text:
        return {"type": "stop", "reason": "empty_response"}
    start = text.find("{")
    if start < 0:
        return {"type": "stop", "reason": "no_json_in_response"}
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if esc:
            esc = False
            continue
        if c == "\\" and in_str:
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                blob = text[start : i + 1]
                try:
                    return json.loads(blob)
                except json.JSONDecodeError:
                    return {"type": "stop", "reason": "json_decode_error", "_raw": blob[:200]}
    return {"type": "stop", "reason": "unbalanced_braces"}


def default_ledger(spine: str, model: str) -> CostLedger:
    return CostLedger(path=HERE / "results" / "cost_ledger.jsonl")
