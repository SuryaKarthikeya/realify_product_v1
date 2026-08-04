"""Sandbox scenario manifests (agency-plan P7, R6, R9). Each scenario is a deterministic spec consumed
by realify.agency.sandbox to build a demo-grade world (SKUs, connections, envelopes, decisions).
Scenarios are data, not code paths.

R9: the old mixed `pilot` (5 USD · 3 INR) is RETIRED and split into two single-country Realify presets —
`us_pilot` (USD, Amazon/Walmart/Shopify) and `in_pilot` (₹ lakh, Flipkart-heavy, Diwali). `auto_in` is
kept for the P7 determinism test. These are read-only Realify presets; tester-generated worlds are saved
separately (saved_worlds)."""
from . import auto_in, us_pilot, in_pilot

SCENARIOS = {"us_pilot": us_pilot.SPEC, "in_pilot": in_pilot.SPEC, "auto_in": auto_in.SPEC}

# Read-only Realify presets shown in "Pick existing seed" (order matters for display).
PRESETS = ["us_pilot", "in_pilot"]
DEFAULT_SCENARIO = "us_pilot"
