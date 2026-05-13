"""Shared scaffolding for all pattern examples.

Provides:
  - StubLLM: deterministic fake LLM so every example runs offline
  - get_llm(): real LangChain LLM if USE_REAL_LLM=1, else StubLLM
  - log(): tagged structured logging so the trace is readable
  - now_ms(): monotonic timestamp helper
"""
from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from typing import Any


# --- Stub LLM ---------------------------------------------------------------

@dataclass
class StubLLM:
    """A deterministic-ish stand-in. Returns canned responses keyed by prompt prefix.

    Real production code would use ChatAnthropic / ChatOpenAI / ADK LlmAgent.
    """
    name: str = "stub-claude-4"
    canned: dict[str, str] | None = None
    fail_rate: float = 0.0

    def invoke(self, prompt: str, **kwargs: Any) -> str:
        if self.fail_rate and random.random() < self.fail_rate:
            raise RuntimeError(f"[{self.name}] simulated upstream failure")
        if self.canned:
            for key, value in self.canned.items():
                if key in prompt:
                    return value
        # Deterministic-ish fallback
        return json.dumps({"model": self.name, "echo": prompt[:80]})


def get_llm(canned: dict[str, str] | None = None, fail_rate: float = 0.0):
    """Return a real LangChain LLM if USE_REAL_LLM=1, else a StubLLM."""
    if os.getenv("USE_REAL_LLM") == "1":
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
        except Exception:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model="gpt-4o", temperature=0)
    return StubLLM(canned=canned, fail_rate=fail_rate)


# --- Logging ----------------------------------------------------------------

def log(tag: str, msg: str, **kv: Any) -> None:
    extras = " ".join(f"{k}={v!r}" for k, v in kv.items())
    print(f"[{tag:>14}] {msg}  {extras}".rstrip())


def now_ms() -> int:
    return int(time.monotonic() * 1000)
