"""Agency console DB seam. Agency code is Postgres-only and speaks raw psycopg (%s) — consistent with
the P1 ledger/ops modules — so it gets a direct psycopg connection from the configured DATABASE_URL
(realify_app in prod; the harness owner/app in tests). Also the agency-level append-only ops audit."""
import json

import psycopg

from .. import config


def agency_connect():
    """A raw psycopg connection to the configured Postgres DB. Agency tables are Postgres-only."""
    url = config.DATABASE_URL
    scheme = url.split("://", 1)[0].split("+", 1)[0].lower()
    if scheme not in ("postgresql", "postgres"):
        raise RuntimeError("agency console requires a Postgres DATABASE_URL")
    return psycopg.connect(url.replace("postgresql+psycopg://", "postgresql://"))


def audit(cur, actor, action, agency_id=None, tenant_id=None, detail=None, reason=None):
    """Append one agency-level ops event (append-only). Actor/ts/reason captured for every entry."""
    cur.execute(
        "INSERT INTO agency_audit(actor, action, agency_id, tenant_id, detail, reason) "
        "VALUES(%s,%s,%s,%s,%s::jsonb,%s) RETURNING id",
        (actor, action, agency_id, tenant_id, json.dumps(detail or {}), reason))
    return cur.fetchone()[0]
