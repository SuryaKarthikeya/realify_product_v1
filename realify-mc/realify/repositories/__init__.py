"""Repository layer (workstream 1b of #005).

The repository layer is the ONLY place that talks to the database. Domain/service/API code
calls repositories (or a UnitOfWork), never raw SQL. This decouples business logic from the
storage engine so the SQLite -> RDS Postgres swap (1c) and RLS tenant isolation (1d) are a
change *here*, not across the codebase.

Two ways to use it:

1. UnitOfWork (preferred for new code) — bundles a connection + the repositories sharing it,
   commits on clean exit, rolls back on exception, always closes:

       from .repositories import UnitOfWork
       with UnitOfWork() as uow:
           user = uow.users.get_by_email(email)
           tid  = uow.tenants.create(name)

2. A caller-managed connection (the legacy path db.py delegates through):

       TenantRepository(con).get(tenant_id)

Transactions today: repository write methods commit individually (preserving the pre-1b
behavior of db.py). The UnitOfWork commit/rollback is belt-and-suspenders for now; when 1c
moves to Postgres, per-method commits are removed and the UnitOfWork becomes the single
transaction boundary (and the place ``SET LOCAL app.tenant_id`` is issued for RLS, 1d).
"""
from .. import db
from .base import BaseRepository
from .tenant_repo import TenantRepository
from .user_repo import UserRepository
from .invite_repo import InviteRepository
from .settings_repo import SettingsRepository
from .pull_repo import PullLogRepository
from .metrics_repo import MetricsRepository
from .card_repo import CardRepository
from .seller_repo import SellerRepository
from .rules_repo import RulesRepository
from .catalog_repo import CatalogRepository
from .order_repo import OrderRepository
from .fact_repos import TrafficRepository, InventoryRepository, SettlementRepository
from .channel_repo import (
    ProductRepository, ChannelListingRepository, ReturnsRepository,
    StorageFeeRepository, ChannelRepository, ChannelEconomicsRepository,
)
from .market_repo import MarketRepository
from .action_repo import ActionRepository
from .analytics_repo import AnalyticsRepository, SystemRepository

__all__ = [
    "BaseRepository", "TenantRepository", "UserRepository", "InviteRepository",
    "SettingsRepository", "PullLogRepository", "MetricsRepository", "CardRepository",
    "SellerRepository", "RulesRepository", "CatalogRepository", "OrderRepository",
    "TrafficRepository", "InventoryRepository", "SettlementRepository",
    "ProductRepository", "ChannelListingRepository", "ReturnsRepository",
    "StorageFeeRepository", "ChannelRepository", "ChannelEconomicsRepository",
    "MarketRepository", "ActionRepository", "AnalyticsRepository", "SystemRepository",
    "UnitOfWork",
]


class UnitOfWork:
    """A connection plus the repositories that share it. ``tenant_id`` is recorded now and
    becomes the RLS context in Phase 1d (``SET LOCAL app.tenant_id`` on enter)."""

    def __init__(self, tenant_id=None):
        self.tenant_id = tenant_id
        self.con = None

    def __enter__(self):
        self.con = db.connect()
        # Phase 1d (Postgres): if self.tenant_id -> self.con.execute("SET LOCAL app.tenant_id=...")
        self.tenants = TenantRepository(self.con)
        self.users = UserRepository(self.con)
        self.invites = InviteRepository(self.con)
        self.settings = SettingsRepository(self.con)
        self.pulls = PullLogRepository(self.con)
        self.metrics = MetricsRepository(self.con)
        self.cards = CardRepository(self.con)
        self.sellers = SellerRepository(self.con)
        self.rules = RulesRepository(self.con)
        self.catalog = CatalogRepository(self.con)
        self.orders = OrderRepository(self.con)
        self.traffic = TrafficRepository(self.con)
        self.inventory = InventoryRepository(self.con)
        self.settlements = SettlementRepository(self.con)
        self.products = ProductRepository(self.con)
        self.listings = ChannelListingRepository(self.con)
        self.returns = ReturnsRepository(self.con)
        self.storage_fees = StorageFeeRepository(self.con)
        self.channels = ChannelRepository(self.con)
        self.channel_economics = ChannelEconomicsRepository(self.con)
        self.market = MarketRepository(self.con)
        self.actions = ActionRepository(self.con)
        self.analytics = AnalyticsRepository(self.con)
        self.system = SystemRepository(self.con)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self.con.commit()
            else:
                self.con.rollback()
        finally:
            self.con.close()
        return False  # never suppress exceptions

    def commit(self):
        self.con.commit()
