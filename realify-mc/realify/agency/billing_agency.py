"""Agency billing (agency-plan P6). Stripe is TEST MODE ONLY — the key must start with sk_test_, else
we refuse. Stripe API calls are isolated + mockable (skipped in CI; a separate opt-in integration test
hits the real test-mode API). The billing MATH is pure integer minor units and needs no Stripe.

Reconciliation invariant: Σ metering events == usage records == invoice lines == Σ per-client
allocation, to the minor unit — held exact by using a largest-remainder split for the prorated base
so the per-client base allocations always sum back to the base total."""
from . import fx, money, metering, pilots

STRIPE_TEST_PREFIX = "sk_test_"


class StripeModeError(Exception):
    pass


def require_test_mode(stripe_key):
    """Refuse anything that isn't a Stripe TEST-mode secret key."""
    if not (stripe_key or "").startswith(STRIPE_TEST_PREFIX):
        raise StripeModeError("Stripe key must be a TEST-mode key (sk_test_...) — refusing")
    return True


def stripe_client(stripe_key):
    """Return the stripe SDK pinned to a TEST-mode key. The ONLY place real Stripe calls originate;
    exercised only by the opt-in integration test (mocked/skipped in CI)."""
    require_test_mode(stripe_key)
    import stripe
    stripe.api_key = stripe_key
    return stripe


def sync_customer(stripe_key, agency_name, email):
    return stripe_client(stripe_key).Customer.create(name=agency_name, email=email)


# ---- pure billing math (property-tested) ----
def allocate(per_client_qty, usage_unit_price_minor, base_total_minor):
    """Per-client lines: usage = qty × unit price; base_total split by qty share via largest-remainder
    so Σ base == base_total exactly (proration-safe). Returns {client: {qty,usage,base,total}}."""
    lines = {c: {"qty": q, "usage_usd_minor": q * usage_unit_price_minor, "base_usd_minor": 0}
             for c, q in per_client_qty.items()}
    clients = list(per_client_qty)
    total_qty = sum(per_client_qty.values())
    if not clients:
        return lines
    if total_qty == 0:                                       # no usage -> split base evenly
        each, rem = divmod(base_total_minor, len(clients))
        for i, c in enumerate(clients):
            lines[c]["base_usd_minor"] = each + (1 if i < rem else 0)
    else:
        floors = {c: (per_client_qty[c] * base_total_minor) // total_qty for c in clients}
        rem = base_total_minor - sum(floors.values())
        order = sorted(clients, key=lambda c: ((per_client_qty[c] * base_total_minor) % total_qty, c),
                       reverse=True)
        for i in range(rem):
            floors[order[i]] += 1
        for c in clients:
            lines[c]["base_usd_minor"] = floors[c]
    for c in clients:
        lines[c]["total_usd_minor"] = lines[c]["usage_usd_minor"] + lines[c]["base_usd_minor"]
    return lines


def reconciliation_delta(per_client_qty, lines, usage_unit_price_minor, base_total_minor):
    """0 iff metering == usage == lines == allocation (qty) and usage/base amounts tie out (minor)."""
    metering_qty = sum(per_client_qty.values())
    line_qty = sum(l["qty"] for l in lines.values())
    qty_delta = 0 if metering_qty == line_qty else 1
    usage_delta = abs(sum(l["usage_usd_minor"] for l in lines.values()) - metering_qty * usage_unit_price_minor)
    base_delta = abs(sum(l["base_usd_minor"] for l in lines.values()) - base_total_minor)
    return qty_delta + usage_delta + base_delta


# ---- invoice build (DB) ----
def build_invoice(cur, agency_id, brands, as_of, sub, currency="USD", prorate_num=1, prorate_den=1,
                  period_start=None, period_end=None):
    """Build + persist an invoice from metering. `sub` carries pricing. IN agencies get an exact INR
    reference total. A lapsed (read-only) pilot is billed ZERO. Returns (invoice_id, summary)."""
    if pilots.is_read_only(cur, agency_id):
        cur.execute("INSERT INTO invoices(agency_id,currency,total_usd_minor,status) "
                    "VALUES(%s,%s,0,'zeroed_lapsed') RETURNING id", (agency_id, currency))
        return cur.fetchone()[0], {"total_usd_minor": 0, "reconciliation_delta": 0, "lapsed": True}

    qtys = metering.per_client_qty(cur, brands, period_start, period_end)
    for b in brands:
        qtys.setdefault(b, 0)
    base_full = sub["per_account_price_minor"] * len(brands) + sub["platform_fee_minor"]
    base_total = base_full * prorate_num // prorate_den            # prorated base (integer)
    lines = allocate(qtys, sub["usage_unit_price_minor"], base_total)

    usage_total = sum(l["usage_usd_minor"] for l in lines.values())
    total = usage_total + base_total
    fx_id = rate = None
    inr_ref = None
    if currency == "USD" and sub.get("hq_country") == "IN":
        fx_id, rate = fx.get_rate(cur, as_of, "INR")
        inr_ref = money.usd_to_quote_minor(total, rate)

    cur.execute("INSERT INTO invoices(agency_id,period_start,period_end,currency,usage_usd_minor,"
                "base_usd_minor,total_usd_minor,inr_reference_minor,fx_rate_id,status) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'open') RETURNING id",
                (agency_id, period_start, period_end, currency, usage_total, base_total, total,
                 inr_ref, fx_id))
    inv_id = cur.fetchone()[0]
    for c, l in lines.items():
        cur.execute("INSERT INTO invoice_lines(invoice_id,tenant_id,qty,usage_usd_minor,base_usd_minor,"
                    "total_usd_minor) VALUES(%s,%s,%s,%s,%s,%s)",
                    (inv_id, c, l["qty"], l["usage_usd_minor"], l["base_usd_minor"], l["total_usd_minor"]))
    delta = reconciliation_delta(qtys, lines, sub["usage_unit_price_minor"], base_total)
    return inv_id, {"total_usd_minor": total, "usage_usd_minor": usage_total, "base_usd_minor": base_total,
                    "inr_reference_minor": inr_ref, "fx_rate_id": fx_id, "reconciliation_delta": delta}
