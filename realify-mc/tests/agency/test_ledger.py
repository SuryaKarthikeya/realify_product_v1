"""T-P1-06 (one ledger entry per mutation, chain verifies, envelope_version recorded) + tamper
detection + T-P1-09 (crypto-shred: payload unreadable, chain still verifies)."""
import os

import psycopg

from realify.agency import ops, ledger, keyring
from realify.pdp import ENVELOPES

OWNER = os.environ["AGENCY_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")


def _brand(cur):
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('L',now()::text,1) RETURNING id")
    t = cur.fetchone()[0]
    cur.execute("INSERT INTO agencies(name) VALUES('LA') RETURNING id")
    ag = cur.fetchone()[0]
    cur.execute("INSERT INTO users(email,created_at) VALUES(%s,now()::text) RETURNING id",
                (f"actor-{t}@x.com",))          # unique per tenant (users.email is UNIQUE)
    u = cur.fetchone()[0]
    return t, ag, u


def _scope(cur, *tenant_ids):
    cur.execute("SELECT set_config('app.brand_ids', %s, true)", ("{" + ",".join(map(str, tenant_ids)) + "}",))


def _count(cur, t):
    cur.execute("SELECT count(*) FROM ledger WHERE tenant_id=%s", (t,))
    return cur.fetchone()[0]


def test_each_mutation_writes_exactly_one_entry_and_chain_verifies(clean_agency, app_conn):
    c = app_conn
    cur = c.cursor(); t, ag, u = _brand(cur); c.commit()

    steps = []
    cur = c.cursor(); _scope(cur, t)
    n = _count(cur, t); eid = ops.create_engagement(cur, u, ag, t); steps.append(_count(cur, t) - n); c.commit()
    cur = c.cursor(); _scope(cur, t)
    n = _count(cur, t); v = ops.publish_envelope(cur, u, eid, t, ENVELOPES["Full Operate"], {}); steps.append(_count(cur, t) - n); c.commit()
    cur = c.cursor(); _scope(cur, t)
    n = _count(cur, t); ops.grant_role(cur, u, eid, t, u, "analyst"); steps.append(_count(cur, t) - n); c.commit()
    cur = c.cursor(); _scope(cur, t)
    n = _count(cur, t); ops.break_glass(cur, u, eid, t, u, ENVELOPES["Full Operate"], "b@x.com", 3600); steps.append(_count(cur, t) - n); c.commit()
    cur = c.cursor(); _scope(cur, t)
    n = _count(cur, t); ops.revoke_engagement(cur, u, eid, t); steps.append(_count(cur, t) - n); c.commit()

    assert steps == [1, 1, 1, 1, 1]              # exactly one ledger entry per mutation
    assert v == 1                                # first envelope version
    cur = c.cursor(); _scope(cur, t)
    cur.execute("SELECT action, envelope_version FROM ledger WHERE tenant_id=%s ORDER BY seq", (t,))
    rows = cur.fetchall()
    actions = [r[0] for r in rows]
    for m in ops.MUTATIONS:
        assert m in actions, m
    assert ("envelope.publish", 1) in [(a, ev) for a, ev in rows]   # envelope_version recorded
    assert ledger.verify_chain(cur, t) is True
    c.commit()


def test_tamper_breaks_the_chain(clean_agency, app_conn):
    c = app_conn
    cur = c.cursor(); t, ag, u = _brand(cur); c.commit()
    cur = c.cursor(); _scope(cur, t)
    eid = ops.create_engagement(cur, u, ag, t); ops.grant_role(cur, u, eid, t, u, "viewer"); c.commit()
    cur = c.cursor(); _scope(cur, t); assert ledger.verify_chain(cur, t) is True; c.commit()

    with psycopg.connect(OWNER) as oc, oc.cursor() as ocur:      # tamper as owner, RLS off
        ocur.execute("SET LOCAL row_security = off")
        ocur.execute("UPDATE ledger SET action='tampered' WHERE tenant_id=%s "
                     "AND seq=(SELECT MIN(seq) FROM ledger WHERE tenant_id=%s)", (t, t))
        oc.commit()

    cur = c.cursor(); _scope(cur, t); assert ledger.verify_chain(cur, t) is False; c.commit()


def test_crypto_shred_makes_payload_unreadable_but_chain_still_verifies(clean_agency, app_conn):
    c = app_conn
    cur = c.cursor(); t, ag, u = _brand(cur); c.commit()
    cur = c.cursor(); _scope(cur, t)
    seq = ledger.append(cur, t, u, "test.payload", payload={"secret": "xyz"}); c.commit()

    cur = c.cursor(); _scope(cur, t)
    assert ledger.read_payload(cur, t, seq) == {"secret": "xyz"}
    assert ledger.verify_chain(cur, t) is True
    keyring.crypto_shred(cur, t); c.commit()

    cur = c.cursor(); _scope(cur, t)
    assert ledger.read_payload(cur, t, seq) is None       # DEK destroyed -> unreadable
    assert ledger.verify_chain(cur, t) is True             # hash over ciphertext -> chain intact
    c.commit()
