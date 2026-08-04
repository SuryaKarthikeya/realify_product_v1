"""R15 Part F — resynth correctness across all five lenses + refresh locale integrity (SQLite/hermetic).

F.9  scheduler.resynthesize(tenant_id, 'full') must run the SAME cross-lens synthesizer the R14 build
     established (NOT a partial/legacy path): after a resynth ALL FIVE lenses repopulate non-empty,
     world-consistent and locale-correct, Profit & Ads per-SKU recoverable still agrees with the
     "Cut ACoS" decisions (decisions ⊆ lens — the R14 source-of-truth reconcile), and a fixed seed
     yields byte-identical ad output.
F.2  scheduler.start_market_refresh must PRESERVE the brand's locale/currency (never rewrite the
     tenant's stored country), for both US ($) and IN (₹).

Mirrors tests/test_card_write.py's provisioning harness (TestClient signup → tester → synthetic
onboard → poll), then calls scheduler.resynthesize / scheduler.start_market_refresh directly.
"""
import os, tempfile, sys, time

_TMP = tempfile.mkdtemp(prefix="realify_r15f_test_")
os.environ["REALIFY_DB"] = os.path.join(_TMP, "test.db")
# Hermetic + deterministic: fixture mode BEFORE importing config (no live Keepa/News calls).
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, api, scheduler, country          # noqa: E402
from run import make_app                                  # noqa: E402
from fastapi.testclient import TestClient                 # noqa: E402

# A seed the injector maps to several _b_high_tacos SKUs rolling tacos > 22, so the R14 reconcile
# (decisions ⊆ lens) is actually exercised — not vacuously satisfied.
_FIXED_SEED = 123


def _seed(cc, n=16):
    """A minimal upload seed (asin/cogs/category/price) so a US tenant can onboard synthetically —
    the bundled 'sample' catalog is India-only (onboarding forces it to IN), so US must go via the
    upload path. Prices land in the target market's band; economics are derived by expand_minimal_seed."""
    lo, hi = (9.99, 69.99) if cc == "US" else (399.0, 2499.0)
    cats = ["Home", "Kitchen", "Beauty", "Outdoors"]
    rows = []
    for i in range(n):
        price = round(lo + (hi - lo) * (i / (n - 1)), 2)
        rows.append({"asin": f"B0{cc}{i:05d}", "cogs": round(price * 0.4, 2),
                     "category": cats[i % len(cats)], "price": price})
    return rows


def _provision(email, cc):
    for suffix in ("", "-wal", "-shm"):
        try: os.remove(os.environ["REALIFY_DB"] + suffix)
        except OSError: pass
    db.init_db()
    c = TestClient(make_app())
    from realify import auth as _auth
    _auth.signup(email, "password1")
    c.post("/api/login", json={"email": email, "password": "password1"})
    c.post("/api/account/type", json={"account_type": "tester"})
    c.post("/api/onboard", json={"mode": "synthetic", "source": "upload",
                                 "country": cc, "seed": _seed(cc)})
    for _ in range(80):
        if c.get("/api/onboard/status").json().get("pct", 0) >= 100:
            break
        time.sleep(0.5)
    con = db.connect()
    tid = con.execute("SELECT tenant_id FROM users WHERE email=?", (email,)).fetchone()["tenant_id"]
    con.close()
    return c, tid


def _counts(tid):
    """Row counts backing each of the five lenses (independent of the API layer)."""
    con = db.connect()
    q = lambda sql: con.execute(sql, (tid,)).fetchone()[0]
    out = {
        "cards":             q("SELECT COUNT(*) FROM cards WHERE tenant_id=?"),
        "ad_performance":    q("SELECT COUNT(*) FROM ad_performance WHERE tenant_id=?"),
        "sku_revenue":       q("SELECT COUNT(*) FROM sku_revenue_period WHERE tenant_id=?"),
        "channels":          q("SELECT COUNT(*) FROM channels WHERE tenant_id=?"),
        "channel_economics": q("SELECT COUNT(*) FROM channel_economics WHERE tenant_id=?"),
        "seller_skus":       q("SELECT COUNT(*) FROM seller_skus WHERE tenant_id=?"),
    }
    con.close()
    return out


def _ad_rows(tid):
    con = db.connect()
    rows = con.execute(
        "SELECT internal_sku, period_start, grain, spend, sales FROM ad_performance "
        "WHERE tenant_id=? ORDER BY internal_sku, period_start", (tid,)).fetchall()
    con.close()
    return [tuple(r) for r in rows]


def _assert_all_lenses_nonempty(tid):
    ct = _counts(tid)
    for lens in ("cards", "ad_performance", "sku_revenue", "channels", "channel_economics", "seller_skus"):
        assert ct[lens] > 0, f"lens '{lens}' empty after resynth: {ct}"
    # API-level: Intelligence feed + Category Analyst both render rows
    assert len(api.get_feed(tid)) > 0, "Intelligence feed empty after resynth"
    assert len(api.get_categories(tid)) > 0, "Category Analyst empty after resynth"
    return ct


def _cmaa_skus(c):
    r = c.get("/api/cmaa").json()
    assert r.get("ok") and not r.get("sample"), f"Profit & Ads returned no real data: {r}"
    return {row["sku"]: row for row in r["skus"]}


def _reconcile_decisions_subset_of_lens(c, tid):
    """R14 source-of-truth reconcile: every SKU the 'Cut ACoS' decision fires on (tacos > 22, judged
    with ad spend) must show a positive recoverable (above_breakeven) in Profit & Ads — decisions ⊆ lens."""
    con = db.connect()
    flagged = con.execute(
        "SELECT internal_sku, asin FROM seller_skus WHERE tenant_id=? AND tacos>22 AND cogs IS NOT NULL",
        (tid,)).fetchall()
    con.close()
    rows = _cmaa_skus(c)
    checked = 0
    for r in flagged:
        sku = r["internal_sku"] or r["asin"]
        card = rows.get(sku)
        if not card or not card.get("judged"):
            continue
        checked += 1
        assert (card.get("above_breakeven") or 0) > 0, \
            f"reconcile broken: SKU {sku} (tacos>22) has recoverable {card.get('above_breakeven')} — decision not reflected in lens"
    assert checked > 0, "reconcile not exercised — no judged tacos>22 SKU (pick a seed that produces one)"
    return checked


def test_resynth_full_us_all_lenses_currency_and_reconcile():
    c, tid = _provision("r15f_us@x.com", "US")
    assert country.tenant_profile(tid)["symbol"] == "$"
    res = scheduler.resynthesize(tid, mode="full", seed=_FIXED_SEED)
    assert res.get("ok"), f"resynth failed: {res}"
    # all five lenses repopulate non-empty
    _assert_all_lenses_nonempty(tid)
    # currency/locale preserved through the resynth
    assert country.tenant_country(tid) == "US"
    assert country.tenant_profile(tid)["symbol"] == "$"
    assert _cmaa_skus(c) and c.get("/api/cmaa").json()["synthetic"] is True
    # Profit & Ads per-SKU recoverable agrees with the Cut-ACoS decisions
    _reconcile_decisions_subset_of_lens(c, tid)


def test_resynth_full_in_preserves_rupee():
    c, tid = _provision("r15f_in@x.com", "IN")
    assert country.tenant_profile(tid)["symbol"] == "₹"
    res = scheduler.resynthesize(tid, mode="full", seed=_FIXED_SEED)
    assert res.get("ok"), f"resynth failed: {res}"
    _assert_all_lenses_nonempty(tid)
    assert country.tenant_country(tid) == "IN"
    assert country.tenant_profile(tid)["symbol"] == "₹"
    _reconcile_decisions_subset_of_lens(c, tid)


def test_resynth_full_is_deterministic_with_fixed_seed():
    _c, tid = _provision("r15f_det@x.com", "US")
    scheduler.resynthesize(tid, mode="full", seed=_FIXED_SEED)
    first = _ad_rows(tid)
    scheduler.resynthesize(tid, mode="full", seed=_FIXED_SEED)
    second = _ad_rows(tid)
    assert first and first == second, "fixed-seed resynth produced non-identical ad_performance rows"


def test_market_refresh_preserves_locale_us_and_in():
    for email, cc, sym in (("r15f_ref_us@x.com", "US", "$"), ("r15f_ref_in@x.com", "IN", "₹")):
        _c, tid = _provision(email, cc)
        before_country, before_sym = country.tenant_country(tid), country.tenant_profile(tid)["symbol"]
        assert before_country == cc and before_sym == sym
        job = scheduler.start_market_refresh(tid)
        for _ in range(60):
            if job.get("done"):
                break
            time.sleep(0.5)
        assert job.get("done"), "market refresh never finished"
        assert country.tenant_country(tid) == cc, "refresh rewrote the tenant's country"
        assert country.tenant_profile(tid)["symbol"] == sym, "refresh changed the currency symbol"


if __name__ == "__main__":
    for fn in (test_resynth_full_us_all_lenses_currency_and_reconcile,
               test_resynth_full_in_preserves_rupee,
               test_resynth_full_is_deterministic_with_fixed_seed,
               test_market_refresh_preserves_locale_us_and_in):
        fn(); print(f"  PASS  {fn.__name__}")
    print("\n4/4 tests passed")
