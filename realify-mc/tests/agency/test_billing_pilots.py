"""P6 (agency suite): T-P6-02 reconciliation (DB), 03 IN INR reference exact, 04 conversion
ledger-derived, 05 lapse zero charges, 06 bounce suppression, 07 deep-link token bound/expiry."""
import datetime
import os

from realify import config
from realify.agency import (metering, billing_agency, pilots, suppression, approvals, ledger,
                            fx, money, tenancy)
from realify.mail import dev

AS_OF = datetime.date(2026, 7, 14)
DIRECT = os.environ["AGENCY_DATABASE_URL"]


def _agency_brands(cur, n=2):
    cur.execute("INSERT INTO agencies(name) VALUES('BA') RETURNING id")
    ag = cur.fetchone()[0]
    brands = []
    for i in range(n):
        cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES(%s,now()::text,1) RETURNING id",
                    (f"BR{i}",))
        t = cur.fetchone()[0]
        cur.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s,%s,'active')", (ag, t))
        brands.append(t)
    return ag, brands


def _sub(hq="US"):
    return {"per_account_price_minor": 10000, "platform_fee_minor": 5000,
            "usage_unit_price_minor": 50, "hq_country": hq}


# ---- T-P6-02 ----
def test_reconciliation_db_delta_zero(owner_conn):
    cur = owner_conn.cursor()
    ag, brands = _agency_brands(cur, n=3)
    owner_conn.commit()
    for i, t in enumerate(brands):
        for _ in range(i + 1):                          # 1,2,3 metering events
            metering.record(cur, t)
    owner_conn.commit()
    inv_id, summ = billing_agency.build_invoice(cur, ag, brands, AS_OF, _sub())
    owner_conn.commit()
    assert summ["reconciliation_delta"] == 0
    cur.execute("SELECT COALESCE(SUM(qty),0) FROM metering_events WHERE tenant_id=ANY(%s)", (brands,))
    metered = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(qty),0) FROM invoice_lines WHERE invoice_id=%s", (inv_id,))
    assert cur.fetchone()[0] == metered == 6


# ---- T-P6-03 ----
def test_in_invoice_inr_reference_exact(owner_conn):
    cur = owner_conn.cursor()
    ag, brands = _agency_brands(cur, n=1)
    fx.lock_rate(cur, AS_OF, "INR", 83_500_000)
    owner_conn.commit()
    metering.record(cur, brands[0])
    owner_conn.commit()
    _, summ = billing_agency.build_invoice(cur, ag, brands, AS_OF, _sub(hq="IN"))
    owner_conn.commit()
    _, rate = fx.get_rate(cur, AS_OF, "INR")
    assert summ["inr_reference_minor"] is not None
    assert summ["inr_reference_minor"] == money.usd_to_quote_minor(summ["total_usd_minor"], rate)


# ---- T-P6-04 ----
def test_conversion_numbers_are_ledger_derived(owner_conn):
    cur = owner_conn.cursor()
    ag, brands = _agency_brands(cur, n=1)
    t = brands[0]
    tenancy.set_brand_scope(cur, [t])
    ledger.append(cur, t, None, "execution.write", payload={})
    ledger.append(cur, t, None, "execution.write", payload={})
    ledger.append(cur, t, None, "approval.approve", payload={})
    owner_conn.commit()
    s = pilots.conversion_summary(cur, ag, brands)
    tenancy.set_brand_scope(cur, [t])
    cur.execute("SELECT count(*) FROM ledger WHERE action='execution.write'")
    ex = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM ledger WHERE action='approval.approve'")
    ap = cur.fetchone()[0]
    assert s["executions_ledgered"] == ex == 2 and s["approvals_ledgered"] == ap == 1


# ---- T-P6-05 ----
def test_lapse_readonly_zero_charges_and_signed_does_not_lapse(owner_conn):
    cur = owner_conn.cursor()
    ag, brands = _agency_brands(cur, n=1)
    pilots.start(cur, ag)
    cur.execute("UPDATE agency_pilots SET started_at=now()-interval '91 days' WHERE agency_id=%s", (ag,))
    owner_conn.commit()
    r = pilots.lapse_job(cur, ag)
    owner_conn.commit()
    assert r["read_only"] is True and r["export_offer"] is True and pilots.is_read_only(cur, ag) is True
    metering.record(cur, brands[0])
    owner_conn.commit()
    _, summ = billing_agency.build_invoice(cur, ag, brands, AS_OF, _sub())     # zero charges after lapse
    owner_conn.commit()
    assert summ["total_usd_minor"] == 0 and summ.get("lapsed") is True

    ag2, _ = _agency_brands(cur, n=1)
    pilots.esign(cur, ag2, "v1", user=None)
    cur.execute("UPDATE agency_pilots SET started_at=now()-interval '120 days' WHERE agency_id=%s", (ag2,))
    owner_conn.commit()
    assert pilots.lapse_job(cur, ag2)["read_only"] is False                    # signed => never lapses


# ---- T-P6-06 ----
def test_bounce_suppresses_and_next_send_refused(owner_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path))
    monkeypatch.setattr(config, "DATABASE_URL", DIRECT, raising=False)          # is_suppressed -> harness PG
    dev.clear()
    cur = owner_conn.cursor()
    notif = {"notificationType": "Bounce", "bounce": {"bounceType": "Permanent",
             "bouncedRecipients": [{"emailAddress": "bounce@simulator.amazonses.com"}]}}
    added = suppression.handle_ses_notification(cur, notif)
    owner_conn.commit()
    assert "bounce@simulator.amazonses.com" in added
    cur.execute("SELECT reason FROM suppression_list WHERE email=%s", ("bounce@simulator.amazonses.com",))
    assert cur.fetchone()[0] == "hard_bounce"                                   # Permanent bounce reason
    from realify import mail
    res = mail.send("bounce@simulator.amazonses.com", "hi", "body")
    assert res.get("suppressed") is True
    assert dev.inbox(to="bounce@simulator.amazonses.com") == []                 # nothing sent
    assert mail.send("ok@example.com", "hi", "body").get("suppressed") is not True


# ---- T-P6-07 (DB: bound to approval + user, expires with the approval) ----
def test_deeplink_token_bound_and_expires_with_approval(owner_conn):
    cur = owner_conn.cursor()
    ag, brands = _agency_brands(cur, n=1)
    t = brands[0]
    tenancy.set_brand_scope(cur, [t])
    cur.execute("INSERT INTO users(email,created_at) VALUES(%s,now()::text) RETURNING id", (f"u-{t}@x.com",))
    u = cur.fetchone()[0]
    cur.execute("SELECT id FROM engagements WHERE tenant_id=%s", (t,))
    eng = cur.fetchone()[0]
    aid = approvals.propose(cur, t, eng, u, "ads", "bid", "s", 1000)
    owner_conn.commit()
    tok = approvals.create_deeplink(cur, aid, u)
    owner_conn.commit()
    assert len(tok) >= 22                                    # >= 128-bit (token_urlsafe(32) = 43 chars)
    assert approvals.validate_deeplink(cur, aid, u, tok) is True
    assert approvals.validate_deeplink(cur, aid, u + 1, tok) is False           # bound to user
    assert approvals.validate_deeplink(cur, aid, u, tok + "x") is False         # bound to token
    cur.execute("UPDATE approvals SET status='rejected' WHERE id=%s", (aid,))
    owner_conn.commit()
    assert approvals.validate_deeplink(cur, aid, u, tok) is False               # expires WITH the approval
