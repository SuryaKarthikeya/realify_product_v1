"""R0 fix 3: the agency maintenance jobs (connection health, day-90 pilot lapse, co-sign expiry) are
scheduled and fire. Compressed-clock: a 91-day-old unsigned pilot lapses; an already-past connection
expires."""
import datetime
import inspect
import os

from realify import config, scheduler
from realify.agency import connections, pilots, tenancy

UTC = datetime.timezone.utc
DIRECT = os.environ.get("AGENCY_DATABASE_URL")


def test_agency_jobs_fire_and_are_wired(owner_conn, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_URL", DIRECT, raising=False)   # run_agency_jobs_once -> harness
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('SchT',now()::text,1) RETURNING id")
    t = cur.fetchone()[0]
    tenancy.set_brand_scope(cur, [t])
    connections.upsert_connection(cur, t, "amazon", "connected",
                                  datetime.datetime.now(UTC) - datetime.timedelta(days=1))   # already past
    cur.execute("INSERT INTO agencies(name) VALUES('SchAg') RETURNING id")
    ag = cur.fetchone()[0]
    pilots.start(cur, ag)
    cur.execute("UPDATE agency_pilots SET started_at = now() - interval '91 days' WHERE agency_id=%s", (ag,))
    owner_conn.commit()

    res = scheduler.run_agency_jobs_once(log=lambda *a, **k: None)
    assert res["connections_expired"] >= 1
    assert res["pilots_lapsed"] >= 1
    owner_conn.rollback()
    assert pilots.is_read_only(cur, ag) is True                        # day-90 lapse applied

    # scheduler config exists: the periodic loop invokes the agency jobs
    assert "run_agency_jobs_once" in inspect.getsource(scheduler._loop)
