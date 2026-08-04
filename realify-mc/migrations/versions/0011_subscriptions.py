"""subscriptions: Stripe billing columns on tenants + grandfather existing tenants

Rolls the (formerly separate) Stripe-billing beta into the main app. A tenant IS the billing entity
(account_type is already per-tenant), so the subscription lives on `tenants`:
  * stripe_customer_id / stripe_subscription_id — Stripe identifiers, looked up by the webhook
  * subscription_status — trialing | active | past_due | canceled | unpaid (plain TEXT for portability;
    the enum is enforced in the app, not a DB CHECK)
  * trial_ends_at / current_period_end — ISO-8601 strings in TEXT on both engines (avoids SQLite's
    TIMESTAMP converter choking on the 'T' separator; the app parses them)

GRANDFATHER: every tenant that already exists when this migration runs is back-filled to
subscription_status='active', so nobody currently using realifyai.app is ever gated by the new
paywall. New tenants created after this point default to NULL and are set explicitly by the signup
paths (public Stripe checkout -> trialing; /superlogin back door -> synthesized active).

Additive, inspector-guarded, safe on fresh and existing DBs (SQLite + Postgres).

Revision ID: 0011_subscriptions
Revises: 0010_topology
"""
from alembic import op
import sqlalchemy as sa

revision = "0011_subscriptions"
down_revision = "0010_topology"
branch_labels = None
depends_on = None

_COLS = [
    ("stripe_customer_id", sa.TEXT()),
    ("stripe_subscription_id", sa.TEXT()),
    ("subscription_status", sa.TEXT()),
    ("trial_ends_at", sa.TEXT()),
    ("current_period_end", sa.TEXT()),
]


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "tenants" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("tenants")}
    for name, typ in _COLS:
        if name not in cols:
            op.add_column("tenants", sa.Column(name, typ))
    # Grandfather everyone who predates the paywall (idempotent: only touches NULLs).
    op.execute("UPDATE tenants SET subscription_status='active' WHERE subscription_status IS NULL")


def downgrade():
    pass
