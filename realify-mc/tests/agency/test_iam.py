"""Email-OTP (6-digit / 10-min / single-use), T-P1-07 revocation, T-P1-08 break-glass."""
import os

import psycopg

from realify.agency import ops, actor, otp, ledger
from realify.mail import dev
from realify.pdp import ENVELOPES, decide, Action

OWNER = os.environ["AGENCY_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")


def _scope(cur, *tenant_ids):
    cur.execute("SELECT set_config('app.brand_ids', %s, true)", ("{" + ",".join(map(str, tenant_ids)) + "}",))


def _mk(cur, name):
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES(%s,now()::text,1) RETURNING id", (name,))
    return cur.fetchone()[0]


def _user(cur, email):
    cur.execute("INSERT INTO users(email,created_at) VALUES(%s,now()::text) RETURNING id", (email,))
    return cur.fetchone()[0]


# ---- email-OTP ----
def test_otp_is_six_digit_single_use_and_expires(app_conn):
    c = app_conn
    cur = c.cursor()
    code = otp.issue(cur, "u@x.com", send=False)
    assert len(code) == 6 and code.isdigit()
    assert otp.verify(cur, "u@x.com", code) is True
    assert otp.verify(cur, "u@x.com", code) is False          # single-use
    wrong = "111111" if code != "111111" else "222222"
    assert otp.verify(cur, "u@x.com", wrong) is False
    c.commit()
    cur = c.cursor()
    code2 = otp.issue(cur, "v@x.com", send=False)
    cur.execute("UPDATE agency_otp SET expires_at = now() - interval '1 minute' WHERE email='v@x.com'")
    assert otp.verify(cur, "v@x.com", code2) is False         # expired
    c.commit()


def test_otp_send_captures_mail(app_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path))
    dev.clear()
    cur = app_conn.cursor()
    code = otp.issue(cur, "brand@x.com", send=True)
    app_conn.commit()
    box = dev.inbox(to="brand@x.com")
    assert len(box) == 1 and code in box[0]["body"]


# ---- T-P1-07 revocation ----
def test_revocation_drops_brand_from_actor_and_leaves_brand_data(clean_agency, app_conn):
    c = app_conn
    cur = c.cursor()
    t1, t2 = _mk(cur, "R1"), _mk(cur, "R2")
    cur.execute("INSERT INTO agencies(name) VALUES('RA') RETURNING id"); ag = cur.fetchone()[0]
    u = _user(cur, "op@x.com")
    # some brand data on t1 (legacy table, app-layer scoped) to prove revocation doesn't delete it
    cur.execute("INSERT INTO seller_skus(tenant_id,asin,title) VALUES(%s,'A1','x'),(%s,'A2','y')", (t1, t1))
    c.commit()

    cur = c.cursor(); _scope(cur, t1, t2)
    e1 = ops.create_engagement(cur, u, ag, t1); e2 = ops.create_engagement(cur, u, ag, t2)
    ops.grant_role(cur, u, e1, t1, u, "analyst"); ops.grant_role(cur, u, e2, t2, u, "analyst")
    c.commit()

    with psycopg.connect(OWNER) as oc, oc.cursor() as ocur:
        assert set(actor.resolve_actor(ocur, u).allowed_tenant_ids) == {t1, t2}

    cur = c.cursor()
    cur.execute("SELECT count(*) FROM seller_skus WHERE tenant_id=%s", (t1,)); before = cur.fetchone()[0]
    _scope(cur, t1); ops.revoke_engagement(cur, u, e1, t1); c.commit()

    with psycopg.connect(OWNER) as oc, oc.cursor() as ocur:
        assert set(actor.resolve_actor(ocur, u).allowed_tenant_ids) == {t2}   # t1 dropped

    cur = c.cursor()
    cur.execute("SELECT count(*) FROM seller_skus WHERE tenant_id=%s", (t1,))
    assert cur.fetchone()[0] == before == 2                                   # brand data untouched
    c.commit()


# ---- T-P1-08 break-glass ----
def test_break_glass_is_readonly_capped_ledgered_notified_and_ttl_bound(clean_agency, app_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path))
    dev.clear()
    c = app_conn
    cur = c.cursor()
    t = _mk(cur, "BG"); cur.execute("INSERT INTO agencies(name) VALUES('BGA') RETURNING id"); ag = cur.fetchone()[0]
    admin = _user(cur, "admin@x.com"); target = _user(cur, "target@x.com")
    c.commit()

    cur = c.cursor(); _scope(cur, t)
    eid = ops.create_engagement(cur, admin, ag, t)
    ops.publish_envelope(cur, admin, eid, t, ENVELOPES["Full Operate"], {})
    gid = ops.break_glass(cur, admin, eid, t, target, ENVELOPES["Full Operate"], "brand@x.com", ttl_seconds=3600)
    c.commit()

    cur = c.cursor(); _scope(cur, t)
    cur.execute("SELECT caps, break_glass, expires_at FROM grants WHERE id=%s", (gid,))
    caps, bg, exp = cur.fetchone()
    assert bg is True and exp is not None
    # read-only and never exceeding the envelope
    for lens, spec in caps.items():
        assert spec["max_kind"] == "read"
        assert decide(ENVELOPES["Full Operate"], caps, Action(lens, "read")).allow
        assert not decide(ENVELOPES["Full Operate"], caps, Action(lens, "execute")).allow
    # ledgered (flagged) + chain intact
    cur.execute("SELECT count(*) FROM ledger WHERE tenant_id=%s AND action='break_glass'", (t,))
    assert cur.fetchone()[0] == 1
    assert ledger.verify_chain(cur, t) is True
    c.commit()

    # brand notified
    box = dev.inbox(to="brand@x.com")
    assert len(box) == 1 and "read-only" in box[0]["body"].lower()

    # TTL: before expiry the target has the brand; after expiry it drops (silence never grants)
    with psycopg.connect(OWNER) as oc, oc.cursor() as ocur:
        assert t in actor.resolve_actor(ocur, target).allowed_tenant_ids
        ocur.execute("SET LOCAL row_security = off")
        ocur.execute("UPDATE grants SET expires_at = now() - interval '1 minute' WHERE id=%s", (gid,))
        oc.commit()
    with psycopg.connect(OWNER) as oc, oc.cursor() as ocur:
        assert t not in actor.resolve_actor(ocur, target).allowed_tenant_ids
