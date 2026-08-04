"""Single source of truth for the brand-scoped agency tables (carry tenant_id, get RLS ENABLE+FORCE
with the current_brand_ids() policy — agency-plan §1c-3). Migrations, the rls_lint test, and the
phase verifier all read this so the set can never drift."""

# P1 core (0015) + P3 (0019) + P4 (0020).
BRAND_SCOPED_TABLES = [
    "engagements", "envelopes", "grants", "brand_keys", "ledger",   # P1
    "connections", "agency_ingest_rows",                            # P3
    "decisions", "rollup_cache",                                    # P4
    "approvals", "executions", "brand_pause",                       # P5
    "metering_events", "invoice_lines",                             # P6
]
