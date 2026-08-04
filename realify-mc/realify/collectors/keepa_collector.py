"""Keepa collector — real market data per ASIN.
LIVE: uses the `keepa` package (domain IN). Keepa returns full history; we keep
only points newer than the last watermark, so re-pulls add just the difference.
FIXTURE: generates a believable snapshot anchored to the seller's own price, with
small drift + occasional competitor undercuts so the cards have real substrate."""
import json, random, hashlib, datetime as dt
from .base import Collector
from .. import db, config
from ..repositories.seller_repo import SellerRepository
from ..repositories.market_repo import MarketRepository

class KeepaCollector(Collector):
    source = "keepa"

    def scopes(self, con):
        return SellerRepository(con).asins(self.tenant_id)

    def run(self, force=False):
        """Live Keepa is pulled in CHUNKED batched queries (a few ASINs each) with
        wait=False so a low token balance RAISES instead of the keepa package sleeping
        (the cause of the hang), and the whole pull is wrapped in a hard wall-clock
        deadline so nothing — not even a library-internal sleep — can stall enrichment.
        Fixture mode stays per-ASIN (local + fast) via the base implementation."""
        if self.mode != "live":
            return super().run(force)
        import socket, threading
        con = db.connect()
        asins = self.scopes(con)
        scope = "ALL"
        started = db.now_iso()
        if not force and not db.due_for_pull(con, self.tenant_id, self.source, scope, self.interval_hours):
            db.record_pull(con, self.tenant_id, self.source, scope, started, "skipped", 0, None, None,
                           note=f"within {self.interval_hours}h interval")
            con.close(); return 0
        frm, to = self.window(con, scope)

        # run the (potentially blocking) keepa work in a worker thread we can abandon
        result = {"records": {"snaps": [], "offers": []}, "note": ""}
        def _work():
            old_to = socket.getdefaulttimeout(); socket.setdefaulttimeout(config.KEEPA_TIMEOUT)
            try:
                result["records"], result["note"] = self.fetch_live_batch(asins)
            except Exception as e:
                result["note"] = f"error: {str(e)[:160]}"
            finally:
                socket.setdefaulttimeout(old_to)
        t = threading.Thread(target=_work, daemon=True); t.start(); t.join(config.KEEPA_DEADLINE)
        if t.is_alive():
            db.record_pull(con, self.tenant_id, self.source, scope, started, "failed", 0, frm, to,
                           note=f"abandoned after {config.KEEPA_DEADLINE}s deadline (token wait?)")
            con.close(); return 0
        records = result["records"]
        n = self.persist(con, scope, records) if records["snaps"] else 0
        status = "ok" if records["snaps"] else "failed"
        db.record_pull(con, self.tenant_id, self.source, scope, started, status, n, frm, to,
                       note=(result["note"] or f"batched {len(asins)} ASINs"))
        con.close(); return n

    def fetch_live_batch(self, asins):
        """One Keepa client, CHUNKED, LIGHTWEIGHT queries with wait=False. The bulk pull
        is deliberately cheap — limited-days history (current snapshot) and offers OFF by
        default — so it fits the token budget instead of failing fast on a heavy request.
        Per-chunk failures are swallowed so a partial pull still records what it got; the
        first failure's reason is surfaced in the note (API key redacted)."""
        import keepa
        domain = self.country_profile()["keepa_domain"]
        api = keepa.Keepa(config.KEEPA_KEY)
        snaps, offers, notes = [], [], []
        chunk = max(1, config.KEEPA_CHUNK)
        want_offers = config.KEEPA_BULK_OFFERS > 0
        for i in range(0, len(asins), chunk):
            part = asins[i:i+chunk]
            try:
                kw = dict(domain=domain, history=True, days=config.KEEPA_BULK_DAYS,
                          buybox=True, wait=False)
                if want_offers: kw["offers"] = config.KEEPA_BULK_OFFERS
                products = api.query(part, **kw) or []
                for p in products:
                    asin = p.get("asin")
                    if not asin: continue
                    snaps.append(self._snapshot_from_keepa(asin, p, db.now_iso()))
                    if want_offers:
                        for off in (p.get("offers") or [])[:config.KEEPA_BULK_OFFERS]:
                            lp = self._offer_landed(off)
                            if lp is None: continue
                            offers.append(dict(asin=asin, seller=off.get("sellerId","?"), price=lp,
                                               is_buybox=int(bool(off.get("isBuyBoxWinner"))),
                                               is_fba=int(bool(off.get("isFBA"))), in_stock=1, condition="new"))
            except Exception as e:
                msg = str(e)[:90]
                if config.KEEPA_KEY: msg = msg.replace(config.KEEPA_KEY, "<key>")
                notes.append(msg)
                continue   # token shortfall / transient — keep going; later chunks may succeed
        self._name_sellers(api, domain, offers)
        note = f"batched {len(snaps)}/{len(asins)} ASINs"
        if notes:
            note += f"; {len(notes)} chunk fail(s); first: {notes[0]}"
        return {"snaps": snaps, "offers": offers}, note

    def _name_sellers(self, api, domain, offers):
        """Replace opaque Keepa sellerIds with human-readable seller names (one batched
        seller_query for all unique ids). A seller's OWN store then shows by name and can be
        told apart from third-party rivals (the reconcile drops own-store offers). Fail-soft:
        an unresolved id keeps its raw value rather than blocking the pull."""
        ids = sorted({o["seller"] for o in offers if o.get("seller") and o["seller"] != "?"})
        if not ids:
            return
        try:
            res = api.seller_query(ids, domain=domain) or {}
            names = {sid: (info.get("sellerName") or sid) for sid, info in res.items()}
        except Exception:
            names = {}
        for o in offers:
            o["seller"] = names.get(o["seller"], o["seller"])

    def country_profile(self):
        from .. import country
        return country.tenant_profile(self.tenant_id)

    # ---------------- LIVE (legacy per-ASIN; kept for single-ASIN drill-down use) ----------------
    def fetch_live(self, con, scope, window_from, window_to):
        import keepa  # only imported in live mode
        api = keepa.Keepa(config.KEEPA_KEY)
        products = api.query(scope, domain=self.country_profile()["keepa_domain"],
                             history=True, offers=20, buybox=True, wait=False)
        p = products[0]
        snaps = [self._snapshot_from_keepa(scope, p, db.now_iso())]
        offers = []
        for off in (p.get("offers") or [])[:20]:
            lp = self._offer_landed(off)
            if lp is None: continue
            offers.append(dict(asin=scope, seller=off.get("sellerId","?"), price=lp,
                               is_buybox=int(bool(off.get("isBuyBoxWinner"))),
                               is_fba=int(bool(off.get("isFBA"))), in_stock=1, condition="new"))
        self._name_sellers(api, self.country_profile()["keepa_domain"], offers)
        return {"snaps": snaps, "offers": offers}

    @staticmethod
    def _offer_landed(off):
        """Current landed price (₹) from a Keepa offer. `offerCSV` is [keepaMinutes, price,
        shipping] triples in CENTS; the LAST triple is current — price=[-2], shipping=[-1].
        (The prior code read [-1]=shipping, which is ~always 0 → every offer priced at ₹0.)
        Returns None for the -1 'no data' sentinel or a malformed CSV so we never store a ₹0
        offer that would fabricate an undercut."""
        csv = off.get("offerCSV") or []
        if len(csv) < 2:
            return None
        price = csv[-2]
        ship = csv[-1] if len(csv) >= 3 else 0
        if price is None or price < 0:
            return None
        ship = ship if (ship and ship > 0) else 0
        return round((price + ship) / 100.0, 2)

    def _snapshot_from_keepa(self, asin, p, captured_at):
        import math
        def cur(key):
            arr = (p.get("data") or {}).get(key)
            if arr is None:
                return None
            # keepa returns history as numpy arrays — never use bare `if arr` (ambiguous
            # truth value). Take the last point, coerce to a native number, and treat
            # keepa's -1 / NaN "no data" sentinels as missing.
            try:
                if len(arr) == 0:
                    return None
                v = arr[-1]
            except TypeError:
                v = arr
            try:
                fv = float(v)
            except (TypeError, ValueError):
                return None
            if math.isnan(fv) or fv < 0:
                return None
            return fv
        return dict(asin=asin, captured_at=captured_at,
                    price=(cur("NEW") or 0),
                    bsr=cur("SALES"), bsr_avg30=cur("SALES"),
                    rating=(cur("RATING") or 0), review_count=cur("COUNT_REVIEWS"),
                    offer_count=cur("COUNT_NEW"),
                    buybox_price=cur("BUY_BOX_SHIPPING"), buybox_seller="?",
                    raw=json.dumps({"asin": asin})[:500])

    # ---------------- FIXTURE ----------------
    def fetch_fixture(self, con, scope, window_from, window_to):
        sku = SellerRepository(con).by_asin(self.tenant_id, scope)
        rnd = random.Random(int(hashlib.md5((scope+window_to[:19]).encode()).hexdigest(), 16) % (2**32))
        own = sku["price"]
        # market price drifts around own price; sometimes a competitor undercuts toward the floor
        market = round(own * rnd.uniform(0.94, 1.08), 2)
        undercut = rnd.random() < 0.35
        bb_price = round(min(market, own * rnd.uniform(0.90, 1.02)), 2) if undercut else round(own, 2)
        bsr = int(rnd.uniform(800, 90000) * (0.4 if sku["rev_share_pct"] > 4 else 1.0))
        if rnd.random() < 0.22:
            bsr30 = int(bsr * rnd.uniform(1.30, 1.80))   # current rank well below 30d avg -> climbing
        else:
            bsr30 = int(bsr * rnd.uniform(0.90, 1.15))
        snap = dict(asin=scope, captured_at=window_to, price=market,
                    bsr=bsr, bsr_avg30=bsr30, rating=sku["rating"],
                    review_count=sku["review_count"] + rnd.randint(0, 8),
                    offer_count=rnd.randint(3, 40),
                    buybox_price=bb_price,
                    buybox_seller=("Autofy" if not undercut else rnd.choice(["MotoShield","RoadArmour","CarKraft"])),
                    raw=json.dumps({"fixture": True}))
        offers = []
        n_off = rnd.randint(2, 6)
        for i in range(n_off):
            comp = rnd.choice(["MotoShield","RoadArmour","CarKraft","ShieldPro","GenericCo"])
            offers.append(dict(asin=scope, seller=comp, price=round(market * rnd.uniform(0.88, 1.12), 2),
                               is_buybox=0, is_fba=int(rnd.random()<0.6), in_stock=int(rnd.random()<0.85),
                               condition="new"))
        if undercut:
            offers.append(dict(asin=scope, seller=snap["buybox_seller"], price=bb_price, is_buybox=1,
                               is_fba=1, in_stock=1, condition="new"))
        return {"snaps": [snap], "offers": offers}

    # ---------------- on-demand DEEP pulls (called by drill-down, not the 4h cycle) ----------------
    def history(self, asin, points=30):
        """Price + BSR time-series for one ASIN. Live parses Keepa CSV history;
        fixture synthesizes a believable 30-point daily series anchored to own price."""
        if self.mode == "live":
            try:
                import keepa
                api = keepa.Keepa(config.KEEPA_KEY)
                p = api.query(asin, domain=self.country_profile()["keepa_domain"], history=True)[0]
                data = p.get("data") or {}
                def series(key_t, key_v):
                    ts = data.get(key_t); vs = data.get(key_v)
                    if ts is None or vs is None: return []
                    out = [{"t": str(t)[:10], "v": float(v)} for t, v in zip(ts, vs) if v and v > 0]
                    return out[-points:]
                return {"price": series("df_NEW", "NEW") or self._fixture_series(asin, points, "price"),
                        "bsr":   series("df_SALES", "SALES") or self._fixture_series(asin, points, "bsr")}
            except Exception:
                pass  # fall through to fixture on any live failure
        return {"price": self._fixture_series(asin, points, "price"),
                "bsr":   self._fixture_series(asin, points, "bsr")}

    def _fixture_series(self, asin, points, kind):
        import datetime as _dt
        con = db.connect()
        row = SellerRepository(con).columns_by_asin(self.tenant_id, asin, ["price", "rev_share_pct"])
        snap = MarketRepository(con).latest_bsr(self.tenant_id, asin)
        con.close()
        base_price = (row["price"] if row else 1500)
        base_bsr = (snap["bsr"] if snap and snap["bsr"] else (int(40000*(0.3 if (row and row["rev_share_pct"]>4) else 1.0)) if row else 30000))
        rnd = random.Random(int(hashlib.md5((asin+kind).encode()).hexdigest(),16)%2**32)
        out=[]; today=_dt.date.today()
        # a gentle trend + noise; price drifts ~5%, bsr can show a climb
        trend = rnd.uniform(-0.0015, 0.0015)
        for i in range(points):
            day=(today - _dt.timedelta(days=points-1-i)).isoformat()
            if kind=="price":
                v=round(base_price*(1+trend*i)*rnd.uniform(0.97,1.03),2)
            else:
                v=int(base_bsr*(1-trend*i*1.5)*rnd.uniform(0.85,1.15))
            out.append({"t":day,"v":v})
        return out

    def find_products(self, con, category, segment, n=8):
        """Products in a category/segment (the 'gap'). Live uses Keepa product_finder;
        fixture synthesizes believable competitor SKUs. Cached in category_products."""
        from ..repositories.catalog_repo import CatalogRepository
        catalog = CatalogRepository(con)
        cached = catalog.cached_segment(self.tenant_id, segment)
        if cached:
            return cached
        rows = self._find_live(category, segment, n) if self.mode=="live" else self._find_fixture(category, segment, n)
        for r in rows:
            catalog.insert_product(self.tenant_id, category, segment, r["asin"], r["title"], r["brand"], r["price"], r["bsr"], r["reviews"], r["rating"])
        con.commit()
        return rows

    def _find_live(self, category, segment, n):
        try:
            import keepa
            api = keepa.Keepa(config.KEEPA_KEY)
            # product_finder: filter by category + (optionally) price/bsr; returns ASINs, then query for detail
            params = {"title": segment, "productType": 0, "perPage": n,
                      "sort": [["current_SALES", "asc"]]}
            _dom = self.country_profile()["keepa_domain"]
            asins = api.product_finder(params, domain=_dom)[:n]
            prods = api.query(asins, domain=_dom, history=False) if asins else []
            out=[]
            for p in prods:
                d=(p.get("data") or {})
                out.append(dict(asin=p.get("asin","?"), title=(p.get("title") or "")[:120],
                                brand=p.get("brand") or "?",
                                price=((d.get("NEW") or [0])[-1]) if d.get("NEW") else 0,
                                bsr=((d.get("SALES") or [0])[-1]) if d.get("SALES") else 0,
                                reviews=p.get("reviewCount") or 0, rating=(p.get("rating") or 0)/10.0))
            return out
        except Exception:
            return self._find_fixture(category, segment, n)

    def _find_fixture(self, category, segment, n):
        rnd = random.Random(int(hashlib.md5(segment.encode()).hexdigest(),16)%2**32)
        brands=["MotoShield","RoadArmour","CarKraft","ShieldPro","AutoElite","DriveMax","GuardX"]
        out=[]
        for i in range(n):
            price=round(rnd.uniform(400,4500),0)
            out.append(dict(asin=f"B0{rnd.randint(10**8,10**9-1)}",
                title=f"{rnd.choice(brands)} {segment.title()} — {rnd.choice(['Premium','Heavy-Duty','Waterproof','Universal','Custom-Fit'])}",
                brand=rnd.choice(brands), price=price,
                bsr=int(rnd.uniform(1500,120000)), reviews=rnd.randint(8,1400),
                rating=round(rnd.uniform(3.6,4.7),1)))
        return out
    def persist(self, con, scope, records):
        n = 0
        for s in records["snaps"]:
            MarketRepository(con).insert_snapshot(self.tenant_id, s["asin"], s["captured_at"], s["price"], s["bsr"], s["bsr_avg30"], s["rating"],
                 s["review_count"], s["offer_count"], s["buybox_price"], s["buybox_seller"], s["raw"])
            n += con.total_changes and 1 or 0
        for o in records["offers"]:
            MarketRepository(con).insert_offer(self.tenant_id, o.get("asin", scope), o.get("captured_at") or records["snaps"][0]["captured_at"] if records["snaps"] else db.now_iso(),
                 o["seller"], o["price"], o["is_buybox"], o["is_fba"], o["in_stock"], o["condition"])
        con.commit()
        return len(records["snaps"]) + len(records["offers"])
