"""Tier C collectors — the open/web-signal layer.
Each is a separate source (own watermark + cadence), writing to tierc_signals.
LIVE paths use free official/freemium sources; FIXTURE seeds realistic, category-
matched signals so the news/recall/trend/social cards fire in the sandbox.
All incremental: query only items published after the last watermark."""
import json, random, hashlib, datetime as dt
from .base import Collector
from .. import db, config
from ..repositories.market_repo import MarketRepository

def _dedup(source, title, published):
    return hashlib.md5(f"{source}|{title}|{published[:10]}".encode()).hexdigest()

def _insert(con, tenant_id, source, signal_type, published_at, category, title, url, summary, confidence, raw):
    MarketRepository(con).insert_signal(tenant_id, source, signal_type, db.now_iso(), published_at, category, title, url, summary,
        confidence, json.dumps(raw)[:600], _dedup(source, title, published_at))

CATS = ["Car Accessories", "Car Electronics", "Bike Accessories", "Other Accessories"]

class _TierC(Collector):
    signal_type = "news"
    def persist(self, con, scope, records):
        for r in records:
            _insert(con, self.tenant_id, self.source, r["signal_type"], r["published_at"], r["category"],
                    r["title"], r["url"], r["summary"], r["confidence"], r.get("raw", {}))
        con.commit()
        return len(records)

# ---------------- RECALLS (region-driven by config.RECALL_REGION: IN | US | BOTH) ----------------
class RecallsCollector(_TierC):
    source = "recalls"; signal_type = "recall"

    def fetch_live(self, con, scope, window_from, window_to):
        from .. import country
        region = country.tenant_profile(self.tenant_id)["recall_region"]
        out = []
        if region in ("US", "BOTH"):
            out += self._fetch_us(window_from, window_to)
        if region in ("IN", "BOTH"):
            out += self._fetch_in(window_from, window_to)
        return out

    def _fetch_us(self, window_from, window_to):
        """US CPSC SaferProducts REST (free)."""
        import requests
        out = []
        try:
            d = window_from[:10]
            url = f"https://www.saferproducts.gov/RestWebServices/Recall?format=json&RecallDateStart={d}"
            for it in (requests.get(url, timeout=config.SOURCE_TIMEOUT).json() or [])[:15]:
                out.append(dict(signal_type="recall", published_at=(it.get("RecallDate") or window_to)[:19],
                                category="Car Accessories", title="[US] "+it.get("Title","Recall"),
                                url=it.get("URL",""), summary=(it.get("Description") or "")[:240],
                                confidence=4, raw={"region":"US"}))
        except Exception:
            pass
        return out

    def _fetch_in(self, window_from, window_to):
        """India recall/safety signals. India has no single CPSC-equivalent REST API;
        practical live sources are BIS product-recall listings and the Govt of India
        open-data portal (data.gov.in) recall datasets. Wire whichever you have access to.
        Left as a guarded fetch so it fails soft (logs, returns []) until an endpoint/key
        is configured, rather than silently returning irrelevant US data."""
        import requests, os
        out = []
        api_key = os.environ.get("DATA_GOV_IN_KEY", "")
        resource = os.environ.get("DATA_GOV_IN_RECALL_RESOURCE", "")  # dataset resource id
        if not (api_key and resource):
            return out  # not configured -> no IN recalls this pull (honest empty, not wrong-country)
        try:
            url = (f"https://api.data.gov.in/resource/{resource}"
                   f"?api-key={api_key}&format=json&limit=20")
            for it in (requests.get(url, timeout=config.SOURCE_TIMEOUT).json().get("records", []))[:15]:
                title = it.get("product") or it.get("title") or "Product recall"
                out.append(dict(signal_type="recall", published_at=(it.get("date") or window_to)[:19],
                                category="Car Accessories", title="[IN] "+str(title)[:150],
                                url="https://www.bis.gov.in/", summary=str(it)[:240],
                                confidence=4, raw={"region":"IN"}))
        except Exception:
            pass
        return out

    def fetch_fixture(self, con, scope, window_from, window_to):
        rnd = random.Random(int(hashlib.md5(("recall"+window_to[:10]).encode()).hexdigest(),16)%2**32)
        if rnd.random() < 0.5:   # recalls are episodic
            return []
        from .. import country
        _rr = country.tenant_profile(self.tenant_id)["recall_region"]
        tag = "IN" if _rr in ("IN","BOTH") else "US"
        return [dict(signal_type="recall", published_at=window_to,
            category="Car Accessories",
            title=f"[{tag}] BIS quality order flags phthalate limits on PVC car covers",
            url="https://www.bis.gov.in/",
            summary="Two competitor PVC cover lines fall under a revised phthalate limit and are likely to be delisted. Govt source — confidence maximal.",
            confidence=4, raw={"fixture": True, "region": tag, "competitor_skus": 2})]

# ---------------- NEWS (free tier of NewsAPI/GNews) ----------------
class NewsCollector(_TierC):
    source = "news"; signal_type = "news"
    def fetch_live(self, con, scope, window_from, window_to):
        import requests, urllib.parse
        from .. import country
        out = []
        try:
            terms = country.tenant_terms(self.tenant_id, con)
            primary = terms[0] if terms else "consumer products"
            query = " OR ".join(f'"{t}"' for t in terms)            # catalog-driven, per tenant
            q = urllib.parse.quote(query)
            url = (f"https://newsapi.org/v2/everything?q={q}"
                   f"&from={window_from[:10]}&sortBy=publishedAt&language=en&pageSize=15&apiKey={config.NEWS_API_KEY}")
            for a in requests.get(url, timeout=config.SOURCE_TIMEOUT).json().get("articles", []):
                out.append(dict(signal_type="news", published_at=(a.get("publishedAt") or window_to)[:19],
                                category=primary, title=a.get("title","")[:160],
                                url=a.get("url",""), summary=(a.get("description") or "")[:240],
                                confidence=2, raw={"src": a.get("source",{}).get("name")}))
        except Exception:
            pass
        return out
    def fetch_fixture(self, con, scope, window_from, window_to):
        rnd = random.Random(int(hashlib.md5(("news"+window_to[:10]).encode()).hexdigest(),16)%2**32)
        pool = [
            dict(category="Car Accessories", confidence=2,
                 title="GST rate revision reported on auto-accessory inputs",
                 summary="A reported GST change may raise PVC cover landed cost ~3-4% next quarter, lifting breakeven floors across the PVC line.",
                 url="https://example.com/gst-auto"),
            dict(category="Car Electronics", confidence=2,
                 title="Dashcam demand climbs as insurers push usage-based policies",
                 summary="Insurer programs referencing dashcam footage are reported to be lifting category interest.",
                 url="https://example.com/dashcam-insure"),
        ]
        return [dict(signal_type="news", published_at=window_to, **{k:v for k,v in p.items()}, raw={"fixture":True})
                for p in rnd.sample(pool, k=rnd.randint(1, len(pool)))]

# ---------------- TRENDS (Google Trends best-effort; pytrends in live) ----------------
class TrendsCollector(_TierC):
    source = "trends"; signal_type = "trend"
    def fetch_live(self, con, scope, window_from, window_to):
        from .. import country
        prof = country.tenant_profile(self.tenant_id)
        out = []
        try:
            from pytrends.request import TrendReq
            pt = TrendReq(hl=f"en-{prof['country']}", tz=(330 if prof['country']=='IN' else 360))
            terms = country.tenant_terms(self.tenant_id, con, n=5)   # catalog-driven, per tenant
            primary = terms[0] if terms else "consumer products"
            pt.build_payload(terms, timeframe="now 7-d", geo=prof["trends_geo"])
            df = pt.interest_over_time()
            # related/rising queries add the 'depth' the drill-down surfaces
            related = {}
            try:
                rq = pt.related_queries()
                for t in terms:
                    rising = (rq.get(t) or {}).get("rising")
                    if rising is not None and not rising.empty:
                        related[t] = list(rising["query"].head(5))
            except Exception:
                pass
            for t in terms:
                if t in df:
                    chg = float(df[t].iloc[-1] - df[t].iloc[0])
                    out.append(dict(signal_type="trend", published_at=window_to, category=primary,
                                    title=f"Search trend: '{t}'", url="https://trends.google.com/",
                                    summary=f"7-day interest change {chg:+.0f}", confidence=3,
                                    raw={"term": t, "chg": chg, "geo": prof["trends_geo"],
                                         "related": related.get(t, [])}))
        except Exception:
            pass
        return out
    def fetch_fixture(self, con, scope, window_from, window_to):
        return [
            dict(signal_type="trend", published_at=window_to, category="Bike Accessories",
                 title="Search demand for 'waterproof bike cover' +41% (14d)",
                 url="https://trends.google.com/", confidence=3,
                 summary="Search interest and BSR slope agree — a real climb, not a paid-promo blip.",
                 raw={"term":"waterproof bike cover","chg":41}),
            dict(signal_type="social", published_at=window_to, category="Car Electronics",
                 title="'Car interior makeover' reel format gaining traction",
                 url="https://example.com/social", confidence=1,
                 summary="Social velocity rising around ambient interior lighting; demand not yet confirmed by BSR/search.",
                 raw={"platform":"reels"}),
        ]
