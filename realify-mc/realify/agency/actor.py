"""Actor context — the agency extension of the identity seam (agency-plan §1c-3). From a user id we
resolve the set of brand tenant_ids they may act on, derived from their GRANTS through ACTIVE
engagements, excluding expired break-glass grants. This set feeds set_brand_scope() (RLS) on every
agency request, so revocation (engagement -> terminated) and break-glass TTL take effect immediately.
"""
import datetime
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActorContext:
    user_id: int
    allowed_tenant_ids: tuple = field(default_factory=tuple)
    agency_ids: tuple = field(default_factory=tuple)


def resolve_actor(cur, user_id):
    """Build the ActorContext for user_id. Uses a raw psycopg cursor. Only ACTIVE engagements and
    unexpired grants count — so terminating an engagement or a break-glass grant lapsing drops the
    brand from the allowed set on the next request (fail-closed)."""
    now = datetime.datetime.now(datetime.timezone.utc)
    # Bootstrap: set the transaction-local actor GUC so the actor-selfread RLS policies (migration 0027)
    # let us read THIS user's own grants + their engagements — with no role able to bypass RLS in prod
    # (realify_app AND realify_admin are both NOBYPASSRLS). The result then scopes the request
    # connection via set_brand_scope(). On the harness owner (BYPASSRLS) this GUC is simply harmless.
    cur.execute("SELECT set_config('app.actor_user_id', %s, true)", (str(user_id),))
    cur.execute(
        "SELECT DISTINCT e.tenant_id, e.agency_id "
        "FROM grants g JOIN engagements e ON e.id = g.engagement_id "
        "WHERE g.user_id = %s AND e.status = 'active' "
        "AND (g.expires_at IS NULL OR g.expires_at > %s)",
        (user_id, now))
    tenants, agencies = [], set()
    for tenant_id, agency_id in cur.fetchall():
        tenants.append(tenant_id)
        agencies.add(agency_id)
    return ActorContext(user_id=user_id,
                        allowed_tenant_ids=tuple(sorted(tenants)),
                        agency_ids=tuple(agencies))
