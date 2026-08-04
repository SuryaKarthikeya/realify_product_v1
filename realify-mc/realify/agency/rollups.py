"""Portfolio rollups (agency-plan P4): per-brand GMV / margin / TACoS, USD-normalized via a locked fx
row, materialized into rollup_cache (refresh job). Per-brand values stay in the selling currency;
portfolio totals sum the USD-normalized figures across the actor's allowed brands. Brand data is read
from the legacy float tables at the documented minor-unit seam (round-half-even)."""
from . import fx, money, tenancy


def compute(cur, tenant_id, currency, as_of):
    """Compute + materialize one brand's rollup. Returns the row dict."""
    fx_id, rate = fx.get_rate(cur, as_of, currency)
    cur.execute("SELECT COALESCE(SUM(price*units_month),0), COALESCE(SUM(cogs*units_month),0) "
                "FROM seller_skus WHERE tenant_id=%s", (tenant_id,))
    gmv_f, cogs_f = cur.fetchone()
    cur.execute("SELECT COALESCE(SUM(spend),0) FROM ad_performance WHERE tenant_id=%s", (tenant_id,))
    ad_f = cur.fetchone()[0]
    gmv = int(round(float(gmv_f) * 100))
    cogs = int(round(float(cogs_f) * 100))
    ad = int(round(float(ad_f) * 100))
    margin = gmv - cogs
    tacos_bps = int(round(ad * 10000 / gmv)) if gmv > 0 else 0
    gmv_usd = money.to_usd_minor(gmv, rate)
    margin_usd = money.to_usd_minor(margin, rate)
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute(
        "INSERT INTO rollup_cache(tenant_id,currency,fx_rate_id,gmv_minor,gmv_usd_minor,margin_minor,"
        "margin_usd_minor,tacos_bps) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) "
        "ON CONFLICT (tenant_id) DO UPDATE SET currency=EXCLUDED.currency,fx_rate_id=EXCLUDED.fx_rate_id,"
        "gmv_minor=EXCLUDED.gmv_minor,gmv_usd_minor=EXCLUDED.gmv_usd_minor,margin_minor=EXCLUDED.margin_minor,"
        "margin_usd_minor=EXCLUDED.margin_usd_minor,tacos_bps=EXCLUDED.tacos_bps,refreshed_at=now()",
        (tenant_id, currency, fx_id, gmv, gmv_usd, margin, margin_usd, tacos_bps))
    return {"tenant_id": tenant_id, "currency": currency, "fx_rate_id": fx_id, "gmv_minor": gmv,
            "gmv_usd_minor": gmv_usd, "margin_minor": margin, "margin_usd_minor": margin_usd,
            "tacos_bps": tacos_bps}


def refresh(cur, brands, as_of):
    """Refresh job: brands = [(tenant_id, currency), ...]."""
    return [compute(cur, tid, ccy, as_of) for tid, ccy in brands]


def portfolio(cur, allowed_tenant_ids):
    """Portfolio totals (USD-normalized) across the actor's allowed brands (RLS-scoped)."""
    if not allowed_tenant_ids:
        return {"gmv_usd_minor": 0, "margin_usd_minor": 0, "brands": 0}
    tenancy.set_brand_scope(cur, allowed_tenant_ids)
    cur.execute("SELECT COALESCE(SUM(gmv_usd_minor),0), COALESCE(SUM(margin_usd_minor),0), COUNT(*) "
                "FROM rollup_cache")
    g, m, n = cur.fetchone()
    return {"gmv_usd_minor": g, "margin_usd_minor": m, "brands": n}


def per_brand(cur, allowed_tenant_ids):
    """Per-brand rollups in selling currency (with formatted display) + USD, RLS-scoped."""
    if not allowed_tenant_ids:
        return []
    tenancy.set_brand_scope(cur, allowed_tenant_ids)
    cur.execute("SELECT tenant_id,currency,gmv_minor,gmv_usd_minor,margin_minor,margin_usd_minor,tacos_bps "
                "FROM rollup_cache ORDER BY gmv_usd_minor DESC, tenant_id")
    out = []
    for tid, ccy, gmv, gmv_usd, margin, margin_usd, tacos in cur.fetchall():
        out.append({"tenant_id": tid, "currency": ccy, "gmv_minor": gmv, "gmv_usd_minor": gmv_usd,
                    "margin_minor": margin, "margin_usd_minor": margin_usd, "tacos_bps": tacos,
                    "gmv_display": money.format_money(gmv, ccy),
                    "margin_display": money.format_money(margin, ccy)})
    return out


def roi_projected(cur, allowed_tenant_ids):
    """ROI v1 — PROJECTED, not realized. Sum of the projected impact of decisions the agency actually
    executed (approvals reaching 'executed'). Explicitly labeled 'projected': realized reconciliation
    (measured-vs-do-nothing) is future work and this must never imply a measured counterfactual."""
    if not allowed_tenant_ids:
        return {"projected_impact_usd_minor": 0, "executed": 0, "label": "projected"}
    tenancy.set_brand_scope(cur, allowed_tenant_ids)
    cur.execute("SELECT COALESCE(SUM(impact_usd_minor),0), COUNT(*) FROM approvals WHERE status='executed'")
    total, n = cur.fetchone()
    return {"projected_impact_usd_minor": int(total or 0), "executed": int(n or 0), "label": "projected"}
