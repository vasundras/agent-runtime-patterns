"""Spine implementations for the §7 ablation.

Two spines wrap the same RenewalAgent so we can A/B them on identical scenarios:
  - p3_event_driven.P3SpineAgent — append-only event log; LLM consumes the log.
  - p5_state_machine.P5SpineAgent — durable row + CAS; LLM consumes the row.

Both inherit RenewalAgent and override only `_propose_action`. Everything else
(gate, audit, terminal handling) stays identical so the only delta in §7 is the
spine choice.
"""
