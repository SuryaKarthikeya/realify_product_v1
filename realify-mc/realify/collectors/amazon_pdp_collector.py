"""Amazon PDP collector — live product-detail-page fetch per ASIN.

The seller's OWN listing as a buyer sees it RIGHT NOW: title, current price, rating,
review count, availability, Buy Box seller, hero image, BSR. This complements the
Keepa collector, which owns the parts a PDP can't give you well:

  - Amazon PDP  -> authoritative CURRENT own-listing fields (fresher than Keepa's refresh)
  - Keepa       -> competitor offers, Buy Box winner over time, price/BSR history series

Both write into `keepa_snapshots` (the shared "latest market observation" table). PDP
rows carry raw.source="amazon_pdp" so the serving layer can PREFER the live snapshot
for the "current on Amazon" display and mark it Verified (live site); Keepa rows keep
their source="keepa". Competitor offers still come only from Keepa.

Fails SOFT. Amazon blocks server-side scraping (captcha / 503 / datacenter-IP soft
blocks); on a block, parse-miss or timeout we record the miss and return nothing,
leaving the Keepa/fixture snapshot in place. Never hangs (hard per-request timeout +
the base circuit breaker), never fabricates a number (a field we can't parse is left
NULL, not guessed). Templated on: https://www.amazon.in/dp/<ASIN>?th=1
"""
import json, re, time, html as _html
from .base import Collector
from .. import db, config
from ..repositories.seller_repo import SellerRepository
from ..repositories.market_repo import MarketRepository

# Realistic desktop browser headers. We rotate the UA per attempt (index-derived, no
# RNG — Math.random is unavailable in some runtimes and determinism keeps tests stable).
_UAS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class PdpBlocked(Exception):
    """Amazon served a robot-check / 503 / captcha instead of the product page."""


class AmazonPdpCollector(Collector):
    source = "amazon_pdp"

    # -------- scope: one ASIN per scope so each has its own watermark + interval --------
    def scopes(self, con):
        return SellerRepository(con).asins(self.tenant_id)

    def _marketplace(self):
        from .. import country
        return country.tenant_profile(self.tenant_id).get("marketplace", "amazon.in")

    def url_for(self, asin):
        return f"https://www.{self._marketplace()}/dp/{asin}?th=1"

    # ---------------- LIVE ----------------
    def fetch_live(self, con, scope, window_from, window_to):
        """`scope` is a single ASIN. Returns [snapshot] on success, [] on soft failure."""
        snap = self.refresh(scope)
        return [snap] if snap else []

    def refresh(self, asin):
        """On-demand single-ASIN live fetch (used by fetch_live and by the drill-down
        endpoint). Returns a snapshot dict or None on any block/parse failure."""
        try:
            html = self._fetch_html(self.url_for(asin))
            snap = self._parse(html, asin)
            return snap if snap and (snap.get("price") or snap.get("rating") or snap.get("review_count")) else None
        except Exception:
            return None  # soft: caller keeps the Keepa/fixture snapshot

    def _fetch_html(self, url):
        import requests
        retries = max(1, config.AMAZON_PDP_RETRIES)
        last = None
        for attempt in range(retries):
            headers = {
                "User-Agent": _UAS[attempt % len(_UAS)],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-cache",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none", "Sec-Fetch-User": "?1",
                "Connection": "keep-alive",
            }
            try:
                r = requests.get(url, headers=headers, timeout=config.AMAZON_PDP_TIMEOUT)
                body = r.text or ""
                if r.status_code in (503, 429) or self._looks_blocked(body):
                    last = PdpBlocked(f"HTTP {r.status_code} / robot-check")
                    time.sleep(min(2.0, 0.6 * (attempt + 1)))   # brief backoff, then rotate UA
                    continue
                if r.status_code != 200:
                    last = PdpBlocked(f"HTTP {r.status_code}")
                    continue
                return body
            except requests.RequestException as e:
                last = e
                time.sleep(min(2.0, 0.6 * (attempt + 1)))
        raise last or PdpBlocked("no response")

    @staticmethod
    def _looks_blocked(body):
        head = body[:4000].lower()
        return ("captcha" in head or "robot check" in head
                or "api-services-support@amazon" in head
                or "to discuss automated access" in head
                or "enter the characters you see below" in head)

    # ---------------- PARSING (bs4 if available, regex fallback) ----------------
    def _parse(self, html, asin):
        # Guard against a TRUE variation redirect: if an invalid variant (?th=1) redirects to
        # a different product, the page's currentAsin differs from what we asked for and every
        # field would be mis-attributed. Reviews/ratings are legitimately POOLED across a
        # variation family (siblings share them) — that's fine and the currentAsin still matches
        # the requested child. A mismatch means the WRONG product loaded -> soft miss.
        cur = re.search(r'"currentAsin"\s*:\s*"([A-Z0-9]{10})"', html)
        if cur and cur.group(1) != asin:
            return None

        soup = None
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            soup = None   # degrade to regex-only extraction

        title = self._title(html, soup)
        price = self._price(html, soup)
        rating = self._rating(html, soup)
        reviews = self._reviews(html, soup)
        bsr = self._bsr(html)
        avail = self._availability(html, soup)
        seller = self._seller(html, soup)
        brand = self._brand(html, soup)
        image = self._image(html, soup)

        raw = {"source": "amazon_pdp", "url": self.url_for(asin), "fetched_at": db.now_iso()}
        for k, v in (("title", title), ("brand", brand), ("image", image),
                     ("availability", avail), ("seller", seller)):
            if v:
                raw[k] = v
        return dict(asin=asin, captured_at=db.now_iso(),
                    price=price or 0, bsr=bsr, bsr_avg30=bsr,
                    rating=rating or 0, review_count=reviews, offer_count=None,
                    buybox_price=price, buybox_seller=(seller or "?"),
                    raw=json.dumps(raw)[:900])

    # --- field extractors: try structured selectors, then loose regex; never guess ---
    def _title(self, html, soup):
        if soup:
            el = soup.select_one("#productTitle")
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)[:200]
        m = re.search(r'id="productTitle"[^>]*>\s*(.*?)\s*<', html, re.S)
        return _html.unescape(m.group(1)).strip()[:200] if m else None

    def _price(self, html, soup):
        if soup:
            for sel in (".a-price .a-offscreen", "#corePriceDisplay_desktop_feature_div .a-offscreen",
                        "#priceblock_ourprice", "#priceblock_dealprice", "#corePrice_feature_div .a-offscreen"):
                el = soup.select_one(sel)
                if el and el.get_text(strip=True):
                    v = self._num(el.get_text())
                    if v:
                        return v
        for pat in (r'"a-offscreen">\s*₹?\s*([\d,]+(?:\.\d+)?)',
                    r'priceblock_ourprice[^>]*>\s*₹?\s*([\d,]+(?:\.\d+)?)'):
            m = re.search(pat, html)
            if m:
                v = self._num(m.group(1))
                if v:
                    return v
        return None

    def _rating(self, html, soup):
        if soup:
            el = soup.select_one("#acrPopover")
            if el and el.get("title"):
                m = re.search(r'([\d.]+)', el["title"])
                if m:
                    return float(m.group(1))
            el = soup.select_one("span[data-hook='rating-out-of-text'], i.a-icon-star span.a-icon-alt")
            if el:
                m = re.search(r'([\d.]+)\s*out of', el.get_text())
                if m:
                    return float(m.group(1))
        m = re.search(r'([\d.]+)\s*out of\s*5\s*stars', html)
        return float(m.group(1)) if m else None

    def _reviews(self, html, soup):
        if soup:
            el = soup.select_one("#acrCustomerReviewText")
            if el:
                m = re.search(r'([\d,]+)', el.get_text())
                if m:
                    return int(m.group(1).replace(",", ""))
        m = re.search(r'([\d,]+)\s*(?:ratings|global ratings|customer reviews)', html, re.I)
        return int(m.group(1).replace(",", "")) if m else None

    def _bsr(self, html):
        # "Best Sellers Rank #1,234 in Car & Motorbike" — take the first (most specific) rank.
        m = re.search(r'Best Sellers Rank[^#]*#\s*([\d,]+)', html, re.I)
        return int(m.group(1).replace(",", "")) if m else None

    def _availability(self, html, soup):
        if soup:
            el = soup.select_one("#availability span, #availability")
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)[:80]
        return None

    def _seller(self, html, soup):
        if soup:
            for sel in ("#sellerProfileTriggerId", "#merchant-info a", "#merchant-info"):
                el = soup.select_one(sel)
                if el and el.get_text(strip=True):
                    return el.get_text(strip=True)[:80]
        m = re.search(r'Sold by[^>]*>\s*([^<]{2,60})', html)
        return _html.unescape(m.group(1)).strip() if m else None

    def _brand(self, html, soup):
        if soup:
            el = soup.select_one("#bylineInfo")
            if el and el.get_text(strip=True):
                return re.sub(r'^(Visit the|Brand:)\s*', '', el.get_text(strip=True)).replace(" Store", "")[:60]
        return None

    def _image(self, html, soup):
        if soup:
            el = soup.select_one("#landingImage")
            if el:
                return el.get("data-old-hires") or el.get("src")
        m = re.search(r'"hiRes":"(https://[^"]+?)"', html) or re.search(r'<meta property="og:image" content="([^"]+)"', html)
        return m.group(1) if m else None

    @staticmethod
    def _num(s):
        m = re.search(r'([\d,]+(?:\.\d+)?)', s or "")
        if not m:
            return None
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            return None

    # ---------------- FIXTURE (no-op: Keepa fixture already seeds market data) ----------------
    def fetch_fixture(self, con, scope, window_from, window_to):
        return []

    # ---------------- persist ----------------
    def persist(self, con, scope, records):
        mr = MarketRepository(con)
        for s in records:
            mr.insert_snapshot(self.tenant_id, s["asin"], s["captured_at"], s["price"], s["bsr"],
                               s["bsr_avg30"], s["rating"], s["review_count"], s["offer_count"],
                               s["buybox_price"], s["buybox_seller"], s["raw"])
        con.commit()
        return len(records)
