"""QW-3: channels / channel_economics carry per-SKU synth DATA, so wipe_tenant_data must clear them
(they were absent from TENANT_DATA_TABLES — audit M-1)."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_chw_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, scheduler                                       # noqa: E402
from realify.ingest.synthetic import SyntheticSource                    # noqa: E402
from realify.repositories.tenant_repo import TenantRepository           # noqa: E402


def test_channels_and_economics_wiped():
    with db.connect() as con:
        tid = TenantRepository(con).create("Tester"); db.set_account_type(con, tid, "tester"); con.commit()
    scheduler.provision_own_data(tid, SyntheticSource(), log=lambda *a: None)

    def cnt(t):
        with db.connect() as con:
            return con.execute(f"SELECT COUNT(*) c FROM {t} WHERE tenant_id=?", (tid,)).fetchone()["c"]

    assert cnt("channels") > 0 and cnt("channel_economics") > 0          # synth populated them
    assert "channels" in db.TENANT_DATA_TABLES and "channel_economics" in db.TENANT_DATA_TABLES
    with db.connect() as con:
        db.wipe_tenant_data(con, tid)
    assert cnt("channels") == 0 and cnt("channel_economics") == 0        # wipe now clears them (QW-3)


if __name__ == "__main__":
    test_channels_and_economics_wiped()
    print("channels_wiped OK")
