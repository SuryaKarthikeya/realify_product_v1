"""Central configuration — typed, all overridable by environment variables.

Settings are read from the environment once into a frozen `Settings` dataclass (see
`settings` below), giving one validated place to add configuration. For backward
compatibility every value is ALSO re-exported as a module-level name (`config.DB_PATH`,
`config.MODE`, ...), so existing call sites and the test suite's `config.DB_PATH`
monkeypatch keep working unchanged. New code may read either `config.settings.db_path`
or `config.DB_PATH`.

If a `.env` file exists at the project root (next to run.py) it is loaded first; shell
exports still win over .env (they're not overwritten).
"""
import os
from dataclasses import dataclass, field


def _load_dotenv():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(root, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if val[:1] not in ("'", '"'):
                val = val.split("#", 1)[0]
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


_load_dotenv()


def _modes():
    base = os.environ.get("MODE", "fixture")
    return {
        "keepa":      os.environ.get("MODE_KEEPA",      base),
        "amazon_pdp": os.environ.get("MODE_AMAZON_PDP", base),
        "recalls":    os.environ.get("MODE_RECALLS",    base),
        "news":       os.environ.get("MODE_NEWS",       base),
        "trends":     os.environ.get("MODE_TRENDS",     base),
    }


@dataclass(frozen=True)
class Settings:
    """Typed, immutable snapshot of configuration read from the environment."""
    # Database / server
    db_path: str
    database_url: str
    port: int
    # Per-source mode: "live" | "fixture"
    mode: dict
    # Credentials (only needed in live mode)
    keepa_key: str
    news_api_key: str
    anthropic_api_key: str
    # Marketplace / regional
    keepa_domain: str
    recall_region: str
    news_query: str
    news_country: str
    trends_geo: str
    trends_terms: str
    currency: str
    # Scheduling
    pull_interval_hours: float
    # Session
    session_secret: str
    session_samesite: str
    session_https_only: bool
    # Stripe billing (subscriptions). Empty keys => billing disabled (funnel still renders).
    stripe_secret_key: str
    stripe_publishable_key: str
    stripe_price_id: str
    stripe_webhook_secret: str
    app_url: str
    # Live-source fail-fast
    source_timeout: float
    live_fail_circuit: int
    keepa_timeout: float
    keepa_chunk: int
    keepa_deadline: float
    keepa_bulk_days: int
    keepa_bulk_offers: int
    # Amazon PDP (live product-detail-page fetch)
    amazon_pdp_timeout: float
    amazon_pdp_retries: int
    # Models
    l2_model: str
    model_timeout: float
    # Backfill
    first_pull_backfill_days: int

    @classmethod
    def from_env(cls):
        env = os.environ.get
        dbp = env("REALIFY_DB", os.path.join(os.path.dirname(__file__), "..", "realify_mc.db"))
        return cls(
            db_path=dbp,
            database_url=env("DATABASE_URL") or ("sqlite:///" + os.path.abspath(dbp)),
            port=int(env("REALIFY_PORT", "8001")),
            mode=_modes(),
            keepa_key=env("KEEPA_KEY", ""),
            news_api_key=env("NEWS_API_KEY", ""),
            anthropic_api_key=env("ANTHROPIC_API_KEY", ""),
            keepa_domain=env("KEEPA_DOMAIN", "IN"),
            recall_region=env("RECALL_REGION", "IN").upper(),
            news_query=env("NEWS_QUERY", "car accessories OR car cover OR dashcam"),
            news_country=env("NEWS_COUNTRY", "in"),
            trends_geo=env("TRENDS_GEO", "IN"),
            trends_terms=env("TRENDS_TERMS", "waterproof car cover,car dashcam,bike cover"),
            currency="\u20b9",
            pull_interval_hours=float(env("PULL_INTERVAL_HOURS", "4")),
            session_secret=env("SESSION_SECRET", "dev-only-change-me-in-prod"),
            session_samesite=env("SESSION_SAMESITE", "lax"),
            session_https_only=(env("SESSION_HTTPS_ONLY", "false").lower() in ("1", "true", "yes")),
            stripe_secret_key=env("STRIPE_SECRET_KEY", ""),
            stripe_publishable_key=env("STRIPE_PUBLISHABLE_KEY", ""),
            stripe_price_id=env("STRIPE_PRICE_ID", ""),
            stripe_webhook_secret=env("STRIPE_WEBHOOK_SECRET", ""),
            app_url=(env("APP_URL", "") or "").rstrip("/"),
            source_timeout=float(env("SOURCE_TIMEOUT", "8")),
            live_fail_circuit=int(env("LIVE_FAIL_CIRCUIT", "3")),
            keepa_timeout=float(env("KEEPA_TIMEOUT", "45")),
            keepa_chunk=int(env("KEEPA_CHUNK", "8")),
            keepa_deadline=float(env("KEEPA_DEADLINE", "90")),
            keepa_bulk_days=int(env("KEEPA_BULK_DAYS", "30")),
            keepa_bulk_offers=int(env("KEEPA_BULK_OFFERS", "0")),
            amazon_pdp_timeout=float(env("AMAZON_PDP_TIMEOUT", "12")),
            amazon_pdp_retries=int(env("AMAZON_PDP_RETRIES", "2")),
            l2_model=env("L2_MODEL", "claude-sonnet-4-6"),
            model_timeout=float(env("MODEL_TIMEOUT", "5")),
            first_pull_backfill_days=int(env("FIRST_PULL_BACKFILL_DAYS", "30")),
        )


settings = Settings.from_env()

# ---- Backward-compatible module-level names (sourced from `settings`) ----
DB_PATH = settings.db_path
DATABASE_URL = settings.database_url
PORT = settings.port
MODE = settings.mode
KEEPA_KEY = settings.keepa_key
NEWS_API_KEY = settings.news_api_key
ANTHROPIC_API_KEY = settings.anthropic_api_key
KEEPA_DOMAIN = settings.keepa_domain
RECALL_REGION = settings.recall_region
NEWS_QUERY = settings.news_query
NEWS_COUNTRY = settings.news_country
TRENDS_GEO = settings.trends_geo
TRENDS_TERMS = settings.trends_terms
CURRENCY = settings.currency
PULL_INTERVAL_HOURS = settings.pull_interval_hours
SESSION_SECRET = settings.session_secret
SESSION_SAMESITE = settings.session_samesite
SESSION_HTTPS_ONLY = settings.session_https_only
STRIPE_SECRET_KEY = settings.stripe_secret_key
STRIPE_PUBLISHABLE_KEY = settings.stripe_publishable_key
STRIPE_PRICE_ID = settings.stripe_price_id
STRIPE_WEBHOOK_SECRET = settings.stripe_webhook_secret
APP_URL = settings.app_url
SOURCE_TIMEOUT = settings.source_timeout
LIVE_FAIL_CIRCUIT = settings.live_fail_circuit
KEEPA_TIMEOUT = settings.keepa_timeout
KEEPA_CHUNK = settings.keepa_chunk
KEEPA_DEADLINE = settings.keepa_deadline
KEEPA_BULK_DAYS = settings.keepa_bulk_days
KEEPA_BULK_OFFERS = settings.keepa_bulk_offers
AMAZON_PDP_TIMEOUT = settings.amazon_pdp_timeout
AMAZON_PDP_RETRIES = settings.amazon_pdp_retries
L2_MODEL = settings.l2_model
MODEL_TIMEOUT = settings.model_timeout
FIRST_PULL_BACKFILL_DAYS = settings.first_pull_backfill_days
