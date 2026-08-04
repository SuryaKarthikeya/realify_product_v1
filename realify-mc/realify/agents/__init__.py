"""Agents — the Realify workforce. See AGENTS-ARCHITECTURE.md.

`catalog` = the specialist roster + autonomy ladder + guardrail templates (the framework). `repo` =
persistence (agents, tasks, the hash-chained Autonomy Ledger, pricing scope tables). `service` =
orchestration: list/hire agents, read the ledger, and — for tester/sandbox accounts — seed sample
decisions so the surface demos real. Behavior (an agent ACTING) is gated by
flags.feature_enabled('agents') + the autonomy ladder (start Observe) + Act-held-until-models-live; the
RIA models supply the pricing math (held). This module builds the STRUCTURE, honestly.
"""
