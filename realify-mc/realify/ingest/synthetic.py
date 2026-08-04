"""Synthetic data source — the default path. Wraps the existing generators so they
write scoped to a tenant. In Step 4 this expands to synthesize all 7 reports' worth
of data with injected conditions to trip >=75% of the rule catalog."""
from .base import DataSource
from .. import db
from ..seller import load_seller_data, generate_orders

class SyntheticSource(DataSource):
    mode = "synthetic"
    def __init__(self, seed_skus=None):
        # seed_skus: optional list of {asin, cogs, category,...} the user uploaded.
        # None -> use the bundled Autofy seed (the demo tenant).
        self.seed_skus = seed_skus
    def provision(self, tenant_id):
        n = load_seller_data(tenant_id, skus=self.seed_skus)
        o = generate_orders(tenant_id)
        # give the tester a fully working Profit & Ads (ad + revenue periods) from the same SKUs
        from .synth_cmaa import synthesize_cmaa
        from .. import db as _db
        with _db.connect() as con:
            synthesize_cmaa(con, tenant_id)
            con.commit()
        return {"mode": "synthetic", "skus": n, **o}
