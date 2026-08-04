"""Brand-scoped mutating operations for the agency console. EVERY function here writes exactly one
hash-chained ledger entry (agency-plan §1b). They take a raw psycopg cursor with the brand scope
already set (RLS) and the acting user. Envelopes are versioned — never updated in place.

MUTATIONS lists the operations the route-table test (T-P1-06) drives to prove one-entry-per-mutation.
"""
import datetime
import json

from . import ledger, keyring
from .. import mail


def _jsonb(d):
    return json.dumps(d or {})


def create_engagement(cur, actor_user, agency_id, tenant_id, status="active"):
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s,%s,%s) RETURNING id",
                (agency_id, tenant_id, status))
    eid = cur.fetchone()[0]
    ledger.append(cur, tenant_id, actor_user, "engagement.create",
                  payload={"agency_id": str(agency_id), "status": status}, engagement_id=eid)
    return eid


def publish_envelope(cur, actor_user, engagement_id, tenant_id, caps, ceilings):
    """New version each call (never updated in place); prior versions deactivated."""
    cur.execute("SELECT COALESCE(MAX(version),0) FROM envelopes WHERE engagement_id=%s", (engagement_id,))
    version = cur.fetchone()[0] + 1
    cur.execute("UPDATE envelopes SET active=false WHERE engagement_id=%s", (engagement_id,))
    cur.execute(
        "INSERT INTO envelopes(engagement_id,tenant_id,version,caps,ceilings,active) "
        "VALUES(%s,%s,%s,%s::jsonb,%s::jsonb,true) RETURNING id",
        (engagement_id, tenant_id, version, _jsonb(caps), _jsonb(ceilings)))
    ledger.append(cur, tenant_id, actor_user, "envelope.publish",
                  payload={"caps": caps, "ceilings": ceilings},
                  engagement_id=engagement_id, envelope_version=version)
    return version


def grant_role(cur, actor_user, engagement_id, tenant_id, user_id, role, caps=None):
    cur.execute(
        "INSERT INTO grants(user_id,engagement_id,tenant_id,role,caps) VALUES(%s,%s,%s,%s,%s::jsonb) "
        "ON CONFLICT (user_id,engagement_id) DO UPDATE SET role=EXCLUDED.role, caps=EXCLUDED.caps, "
        "break_glass=false, expires_at=NULL RETURNING id",
        (user_id, engagement_id, tenant_id, role, _jsonb(caps)))
    gid = cur.fetchone()[0]
    ledger.append(cur, tenant_id, actor_user, "grant.create",
                  payload={"user_id": user_id, "role": role}, grant_id=gid, engagement_id=engagement_id)
    return gid


def revoke_engagement(cur, actor_user, engagement_id, tenant_id):
    """Terminate: tokens/grants under it stop resolving; brand data is NOT touched."""
    cur.execute("UPDATE engagements SET status='terminated' WHERE id=%s", (engagement_id,))
    ledger.append(cur, tenant_id, actor_user, "engagement.terminate", engagement_id=engagement_id)


def break_glass(cur, actor_user, engagement_id, tenant_id, target_user, envelope_caps,
                brand_email, ttl_seconds=3600):
    """Time-boxed READ-ONLY elevation, capped so it never exceeds the envelope. Ledgered (flagged) and
    the brand is notified by mail."""
    capped = {lens: {"max_kind": "read", "autonomy_ceiling": int(spec.get("autonomy_ceiling", 0))}
              for lens, spec in (envelope_caps or {}).items()}
    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=ttl_seconds)
    cur.execute(
        "INSERT INTO grants(user_id,engagement_id,tenant_id,role,caps,break_glass,expires_at) "
        "VALUES(%s,%s,%s,'break_glass',%s::jsonb,true,%s) "
        "ON CONFLICT (user_id,engagement_id) DO UPDATE SET role='break_glass', "
        "caps=EXCLUDED.caps, break_glass=true, expires_at=EXCLUDED.expires_at RETURNING id",
        (target_user, engagement_id, tenant_id, _jsonb(capped), expires))
    gid = cur.fetchone()[0]
    mail.send(brand_email, "Break-glass access to your Realify account",
              f"Temporary read-only access was activated on your account until {expires.isoformat()}. "
              f"If this was not expected, contact support.", reply_to="notifications@realifyai.app")
    ledger.append(cur, tenant_id, actor_user, "break_glass",
                  payload={"target_user": target_user, "expires_at": expires.isoformat(),
                           "flagged": True},
                  grant_id=gid, engagement_id=engagement_id)
    return gid


# route-table for T-P1-06 (each writes exactly one ledger entry)
MUTATIONS = ["engagement.create", "envelope.publish", "grant.create",
             "engagement.terminate", "break_glass"]
