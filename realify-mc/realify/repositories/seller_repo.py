"""Seller economics — the `seller_skus` table (the central own-data table).
SQL moved verbatim from seller.py / cogs.py / synth_conditions.py / channels.py /
ingest/seed.py / ingest/report_parse.py / detector_settings paths (workstream 1b).

Write methods do NOT commit — the caller owns the transaction (matches the existing call
sites, which each do their own commit after a batch). NOTE: the economic *formulas*
(net/margin/floor/rev_share) are still computed at the call sites and passed in here as
values; that computation consolidates into `domain/economics.py` in workstream 1e. This
repository owns the *persistence*, not the math.
"""
from .base import BaseRepository

# Columns a caller may target in a dynamic UPDATE / projection. Guards against a stray
# key building unexpected SQL (keys are code-controlled today, but this keeps it safe).
_COLS = {
    "asin", "internal_sku", "channel", "title", "category", "ptype", "amazon_cat", "price",
    "cogs", "referral_fee", "fba_fee", "ad_cost_unit", "return_cost_unit", "net_profit_unit",
    "net_margin_pct", "breakeven_floor", "units_month", "units_year", "velocity_day",
    "annual_rev_inr", "rev_share_pct", "stock_on_hand", "days_of_cover", "buybox_pct",
    "tacos", "returns_rate", "rating", "review_count",
    "replacement_units", "mcf_units", "provisional_units", "lifecycle_flag", "margin_floor",   # 1b: ingested signal + seller-editable
    "title_override",   # seller-set title when the report title is missing/poor (sticky)
    "optimize_for",     # 0009: seller's per-SKU strategy choice (Product Catalog); stored intent only
}

# Exact column order of the seed INSERT (seller.py load_seller_data).
_INSERT_COLS = [
    "tenant_id", "asin", "title", "category", "ptype", "amazon_cat", "price", "cogs",
    "referral_fee", "fba_fee", "ad_cost_unit", "return_cost_unit", "net_profit_unit",
    "net_margin_pct", "breakeven_floor", "units_month", "units_year", "velocity_day",
    "annual_rev_inr", "rev_share_pct", "stock_on_hand", "days_of_cover", "buybox_pct",
    "tacos", "returns_rate", "rating", "review_count",
]


class SellerRepository(BaseRepository):
    # ---------- reads ----------
    def all(self, tenant_id):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM seller_skus WHERE tenant_id=?", (tenant_id,)).fetchall()]

    def by_asin(self, tenant_id, asin):
        r = self.con.execute(
            "SELECT * FROM seller_skus WHERE tenant_id=? AND asin=?", (tenant_id, asin)).fetchone()
        return dict(r) if r else None

    def count(self, tenant_id):
        return self.con.execute(
            "SELECT COUNT(*) c FROM seller_skus WHERE tenant_id=?", (tenant_id,)).fetchone()["c"]

    def count_non_null(self, tenant_id, col):
        if col not in _COLS:
            raise ValueError(f"unknown column {col!r}")
        return self.con.execute(
            f"SELECT COUNT(*) c FROM seller_skus WHERE tenant_id=? AND {col} IS NOT NULL",
            (tenant_id,)).fetchone()["c"]

    def distinct_categories(self, tenant_id):
        return [r["category"] for r in self.con.execute(
            "SELECT DISTINCT category FROM seller_skus WHERE tenant_id=?", (tenant_id,)).fetchall()]

    def category_aggregate(self, tenant_id, category):
        """{n, gmv, bb} for one category (SKU count, summed annual revenue, avg buy-box)."""
        return dict(self.con.execute(
            """SELECT COUNT(*) n, COALESCE(SUM(annual_rev_inr),0) gmv, AVG(buybox_pct) bb
               FROM seller_skus WHERE tenant_id=? AND category=?""", (tenant_id, category)).fetchone())

    def distinct_values(self, tenant_id, col):
        if col not in _COLS:
            raise ValueError(f"unknown column {col!r}")
        return [r["v"] for r in self.con.execute(
            f"SELECT DISTINCT {col} AS v FROM seller_skus WHERE tenant_id=? AND {col} IS NOT NULL AND {col}<>''",
            (tenant_id,)).fetchall()]

    def asins(self, tenant_id, ordered=False):
        q = "SELECT asin FROM seller_skus WHERE tenant_id=?" + (" ORDER BY asin" if ordered else "")
        return [r["asin"] for r in self.con.execute(q, (tenant_id,)).fetchall()]

    def select_columns(self, tenant_id, columns):
        """SELECT a fixed projection (columns is a list of known column names). Returns dicts."""
        for c in columns:
            if c not in _COLS:
                raise ValueError(f"unknown column {c!r}")
        cols = ",".join(columns)
        return [dict(r) for r in self.con.execute(
            f"SELECT {cols} FROM seller_skus WHERE tenant_id=?", (tenant_id,)).fetchall()]

    def price_row_by_sku_or_asin(self, tenant_id, sku):
        """The price row for a SKU (by asin OR internal_sku), or None if no such SKU exists.
        Returns a dict so callers can distinguish 'no row' (None) from 'price is NULL'."""
        r = self.con.execute(
            "SELECT price FROM seller_skus WHERE tenant_id=? AND (asin=? OR internal_sku=?)",
            (tenant_id, sku, sku)).fetchone()
        return dict(r) if r else None

    def columns_by_asin(self, tenant_id, asin, columns):
        """Fixed projection for a single asin; dict or None."""
        for c in columns:
            if c not in _COLS:
                raise ValueError(f"unknown column {c!r}")
        cols = ",".join(columns)
        r = self.con.execute(
            f"SELECT {cols} FROM seller_skus WHERE tenant_id=? AND asin=?", (tenant_id, asin)).fetchone()
        return dict(r) if r else None

    # ---------- writes (no commit; caller owns the transaction) ----------
    def delete_all(self, tenant_id):
        self.con.execute("DELETE FROM seller_skus WHERE tenant_id=?", (tenant_id,))

    def insert(self, tenant_id, s, rev_share_pct):
        """Insert one fully-synthesized SKU row (seller.py load_seller_data). `s` is the row
        dict; rev_share_pct is computed by the caller (needs the tenant GMV total)."""
        vals = (
            tenant_id, s["asin"], s["title"], s["category"], s["ptype"], s["amazon_cat"], s["price"],
            s["cogs"], s["referral_fee"], s["fba_fee"], s["ad_cost_unit"], s["return_cost_unit"],
            s["net_profit_unit"], s["net_margin_pct"], s["breakeven_floor"], s["units_month"],
            s["units_year"], s["velocity_day"], s["annual_rev_inr"], rev_share_pct, s["stock_on_hand"],
            s["days_of_cover"], s["buybox_pct"], s["tacos"], s["returns_rate"], s["rating"], s["review_count"],
        )
        cols = ",".join(_INSERT_COLS); qs = ",".join("?" * len(_INSERT_COLS))
        self.con.execute(f"INSERT OR REPLACE INTO seller_skus({cols}) VALUES({qs})", vals)

    def update_economics(self, tenant_id, sku, cogs, referral, net, margin, floor):
        """COGS + the deterministic economics that follow (cogs.apply, with a price)."""
        self.con.execute(
            "UPDATE seller_skus SET cogs=?, referral_fee=?, net_profit_unit=?, net_margin_pct=?, "
            "breakeven_floor=? WHERE tenant_id=? AND (asin=? OR internal_sku=?)",
            (cogs, referral, net, margin, floor, tenant_id, sku, sku))

    def update_cogs(self, tenant_id, sku, cogs):
        """COGS only (cogs.apply when price is unknown)."""
        self.con.execute(
            "UPDATE seller_skus SET cogs=? WHERE tenant_id=? AND (asin=? OR internal_sku=?)",
            (cogs, tenant_id, sku, sku))

    def get_full(self, tenant_id, sku):
        """Full row (dict) by internal_sku or asin, or None. Used by the 1b ingestion writer to
        merge new report values over existing data without clobbering unrelated columns."""
        r = self.con.execute(
            "SELECT * FROM seller_skus WHERE tenant_id=? AND (internal_sku=? OR asin=?)",
            (tenant_id, sku, sku)).fetchone()
        return dict(r) if r else None

    def upsert_full(self, tenant_id, row):
        """INSERT OR REPLACE a full seller_skus row from a dict (1b report writer). Only known
        columns are written; asin (the PK) must be present. dbengine rewrites OR REPLACE to the
        Postgres ON CONFLICT form."""
        row = {"tenant_id": tenant_id, **{k: v for k, v in row.items() if k in _COLS}}
        cols = list(row)
        self.con.execute(
            f"INSERT OR REPLACE INTO seller_skus({','.join(cols)}) VALUES({','.join('?'*len(cols))})",
            tuple(row[c] for c in cols))

    def update_fields_by_asin(self, tenant_id, asin, fields):
        """Dynamic SET on the named fields, keyed by asin (synth_conditions band injection)."""
        if not fields:
            return
        for k in fields:
            if k not in _COLS:
                raise ValueError(f"unknown column {k!r}")
        sets = ",".join(f"{k}=?" for k in fields)
        self.con.execute(
            f"UPDATE seller_skus SET {sets} WHERE tenant_id=? AND asin=?",
            (*fields.values(), tenant_id, asin))

    def update_fields_by_sku_or_asin(self, tenant_id, sku, fields):
        """Dynamic SET keyed by (asin OR internal_sku) — report_parse field updates."""
        if not fields:
            return
        for k in fields:
            if k not in _COLS:
                raise ValueError(f"unknown column {k!r}")
        sets = ",".join(f"{k}=?" for k in fields)
        self.con.execute(
            f"UPDATE seller_skus SET {sets} WHERE tenant_id=? AND (asin=? OR internal_sku=?)",
            (*fields.values(), tenant_id, sku, sku))

    def normalize_tacos_random(self, tenant_id):
        """synth_conditions: put tacos on a consistent percent scale for non-overridden SKUs.
        Per-row randomness is generated in SQL, but the expression differs by dialect: SQLite's
        RANDOM() is a large signed integer (so ABS(...%900) gives 0..899), whereas Postgres
        random() is a double in [0,1) (floor(...*900) gives 0..899) and ROUND(double, int) is
        undefined there, so the value is cast to numeric before rounding. Both yield 4.0..13.0."""
        from realify import dbengine
        if dbengine.dialect() == "postgresql":
            expr = "ROUND((4 + floor(random()*900)/100.0)::numeric, 1)"
        else:
            expr = "ROUND(4 + ABS(RANDOM()%900)/100.0, 1)"
        self.con.execute(
            f"UPDATE seller_skus SET tacos={expr} WHERE tenant_id=?",
            (tenant_id,))

    def link_channel(self, tenant_id, asin, internal_sku, channel):
        """channels.py: stamp the canonical internal_sku + channel back onto the source row."""
        self.con.execute(
            "UPDATE seller_skus SET internal_sku=?, channel=? WHERE tenant_id=? AND asin=?",
            (internal_sku, channel, tenant_id, asin))

    def backfill_internal_sku(self, tenant_id):
        """Default internal_sku to the canonical 'SKU-'+asin where unset (synth catalog, pre-channels),
        so ad/revenue keys match reads regardless of whether the channel layer has run yet."""
        self.con.execute(
            "UPDATE seller_skus SET internal_sku='SKU-'||asin "
            "WHERE tenant_id=? AND (internal_sku IS NULL OR internal_sku='')", (tenant_id,))
        self.con.commit()
