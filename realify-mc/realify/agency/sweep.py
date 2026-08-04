"""R7 Part 0 — prod hygiene: retire verification/test agencies (and their brand tenants) from the
fleet REVERSIBLY (a flag, never a hard delete), and reap stale VERIFY-* tenants.

Convention (Part 0b): every verification tenant created hereafter MUST be named 'VERIFY-*' AND set
tenant_kind='internal'. The reaper retires VERIFY-* agencies older than N days. Documented in
docs/OPS-VERIFY-CONVENTION.md so phases stop accumulating cruft.

'Retire' = agencies.internal=true (+ the agency's brand tenants tenant_kind='internal'). Both are
reversible flags and are excluded from the default fleet + all billable/revenue aggregates."""

# Name patterns for the categories of verification cruft accumulated across R2–R6. Order matters:
# earlier categories claim an agency first, so counts don't double-count overlaps (see `seen`).
_PATTERNS = [
    ("live_verify", "%Live Verify%"),
    ("feeder_verify", "%Feeder Verify%"),
    ("verify_prefix", "VERIFY-%"),
    ("phase_live", "R_ Live%"),                       # R2/R3/R4 "Live" verification runs
    ("legacy_sandbox_agency", "Sandbox Agency"),      # pre-R6 per-click singletons
]


def _brand_tenants_of(cur, agency_ids):
    if not agency_ids:
        return []
    cur.execute("SELECT DISTINCT tenant_id FROM engagements WHERE agency_id = ANY(%s)", (agency_ids,))
    return [r[0] for r in cur.fetchall()]


def sweep(cur, dry_run=False):
    """Flag matching agencies internal (reversible). Returns counts by category (agencies flagged now)
    plus 'already_internal' (previously retired, incl. R6-retired sandbox singletons) and 'tenants'
    (brand tenants reclassified). Idempotent: re-running flags only what's newly matched."""
    counts = {}
    flagged_ids = []
    seen = set()
    for cat, pat in _PATTERNS:
        cur.execute("SELECT id FROM agencies WHERE name LIKE %s AND NOT COALESCE(internal, false)", (pat,))
        ids = [r[0] for r in cur.fetchall() if r[0] not in seen]    # dedup so overlaps aren't double-counted
        counts[cat] = len(ids)
        seen.update(ids)
        flagged_ids.extend(ids)
    # already-retired (internal flag set, or an R6 sandbox_scenario tag) — reported, not re-touched
    cur.execute("SELECT count(*) FROM agencies WHERE COALESCE(internal, false) "
                "OR sandbox_scenario IS NOT NULL")
    counts["already_internal_or_sandbox"] = cur.fetchone()[0]
    tenants = 0
    if flagged_ids and not dry_run:
        brand_ids = _brand_tenants_of(cur, flagged_ids)
        cur.execute("UPDATE agencies SET internal=true WHERE id = ANY(%s)", (flagged_ids,))
        if brand_ids:
            cur.execute("UPDATE tenants SET tenant_kind='internal', is_internal=true "
                        "WHERE id = ANY(%s) AND tenant_kind='seller'", (brand_ids,))
            tenants = cur.rowcount
    counts["tenants_reclassified"] = tenants
    counts["agencies_flagged_now"] = len(flagged_ids)
    return counts


def unretire(cur, agency_id):
    """Reverse a retirement (the flag is reversible by design)."""
    cur.execute("UPDATE agencies SET internal=false WHERE id=%s", (agency_id,))


def reap_verify(cur, older_than_days=7, dry_run=False):
    """Retire VERIFY-* agencies whose brand tenants were all created more than N days ago. Returns the
    count retired. Intended to run from a scheduled job or `make reap-verify`."""
    cur.execute(
        "SELECT id FROM agencies WHERE name LIKE 'VERIFY-%%' AND NOT COALESCE(internal, false) "
        "AND created_at < now() - make_interval(days => %s)", (int(older_than_days),))
    ids = [r[0] for r in cur.fetchall()]
    if ids and not dry_run:
        brand_ids = _brand_tenants_of(cur, ids)
        cur.execute("UPDATE agencies SET internal=true WHERE id = ANY(%s)", (ids,))
        if brand_ids:
            cur.execute("UPDATE tenants SET tenant_kind='internal', is_internal=true "
                        "WHERE id = ANY(%s) AND tenant_kind='seller'", (brand_ids,))
    return len(ids)
