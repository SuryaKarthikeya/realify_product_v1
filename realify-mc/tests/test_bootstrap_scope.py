"""P1-audit item 6b (R2 update): the actor bootstrap is realify.agency.actor.resolve_actor. It now sets
the transaction-local actor GUC (app.actor_user_id) so the actor-selfread RLS policies (migration 0027)
let it read the user's own grants WITHOUT any RLS bypass (no prod role can bypass). This asserts the
bootstrap still executes ONLY the setup statement + the single grants-resolution query and never reads
brand-data tables — so the bootstrap can't be repurposed to leak brand data. Pure (no DB)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.agency import actor      # noqa: E402


class _RecordingCursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append(sql.strip())

    def fetchall(self):
        return []


def test_resolve_actor_runs_only_setup_plus_single_grants_query():
    cur = _RecordingCursor()
    ctx = actor.resolve_actor(cur, 42)

    assert len(cur.calls) == 2, cur.calls                      # exactly: actor-GUC setup + grants query
    assert "set_config('app.actor_user_id'" in cur.calls[0].lower()   # bootstrap sets the actor GUC (no RLS bypass)
    q = cur.calls[1].lower()
    assert q.startswith("select") and "from grants g join engagements" in q
    # never touches brand-data tables
    for forbidden in ("seller_skus", "cards", "ledger", "envelopes", "brand_keys", "ad_performance"):
        assert forbidden not in q, forbidden
    assert ctx.user_id == 42 and ctx.allowed_tenant_ids == ()
