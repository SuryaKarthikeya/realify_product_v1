"""Ingestion seam. Every data source — synthesize now, real report parsers later —
implements DataSource.provision(tenant_id). They all write into the SAME tenant-scoped
tables, so adding a parser is a new adapter, NOT a schema or pipeline change.

Fast-follow contract for report parsers (Step 6):
  class AmazonReportSource(DataSource):
      def __init__(self, files): ...        # the 7 uploaded report paths
      def provision(self, tenant_id):       # parse -> normalize -> write seller_skus/orders/...
The orchestrator (provision_tenant) doesn't care which adapter it holds."""
from abc import ABC, abstractmethod

class DataSource(ABC):
    mode = "base"
    @abstractmethod
    def provision(self, tenant_id):
        """Populate this tenant's own-data tables (seller_skus, seller_orders, and —
        as the schema grows in Step 3 — traffic/returns/inventory/settlements/listings).
        Returns a dict summary."""
        raise NotImplementedError
