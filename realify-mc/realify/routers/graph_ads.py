"""Read-only proxies to the RIA bot's graph and ad-optimisation endpoints.

  GET /at-risk           graph-ranked at-risk SKUs (the Intelligence 'Why' panel)
  GET /diagnose          per-SKU root-cause traversal — the CONCLUSION
  GET /sku-graph         the neighbourhood that conclusion rests on — the EVIDENCE
  GET /ad-budget-plan    CVaR reallocation of the current ad budget (GATED, see below)

Split out of routers/intelligence.py, which had grown past the 400-line cap that
tests/test_file_length.py enforces. These four belong together and nowhere else: every one is a
thin async proxy over `_bot_get`, none of them touches the app's own database, and none carries model
logic. Paths are unchanged — this module mounts at the same /api prefix, so no client moves.

`/ad-budget-plan` is the only gated route here, behind the same double lock as the held ads model it
depends on (`ads_preview` flag AND tester/grant, via helpers.ads_preview_allowed). The ad effect's
DIRECTION is not identified — sales predict spend as strongly as spend predicts sales — so no seller
sees a confident budget reallocation resting on it. It fails CLOSED with a 404.
"""
import asyncio
import json
import os
import urllib.parse
import urllib.request

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .deps import current, require_tenant

_BOT_URL = os.environ.get("RIA_BOT_URL", "http://localhost:8090").rstrip("/")

router = APIRouter()


def _bot_get(path):
    """GET a bot endpoint and return parsed JSON, or an {ok:false} envelope on failure. Soft-fails so
    a bot that is down degrades one panel instead of erroring the tab."""
    try:
        req = urllib.request.Request(f"{_BOT_URL}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except Exception as e:                       # noqa: BLE001
        return {"ok": False, "error": f"signal-graph service unavailable ({e})"}


@router.get("/at-risk")
async def at_risk(request: Request, limit: int = 8):
    """Graph-ranked at-risk SKUs for the Intelligence 'Why' panel (proxies the bot)."""
    require_tenant(request)
    data = await asyncio.to_thread(_bot_get, f"/v1/at-risk?limit={int(limit)}")
    return JSONResponse(data)


@router.get("/diagnose")
async def diagnose(request: Request, sku: str):
    """Per-SKU root-cause 'why' traversal over the signal graph (proxies the bot)."""
    require_tenant(request)
    q = urllib.parse.quote((sku or "").strip())
    data = await asyncio.to_thread(_bot_get, f"/v1/diagnose?sku={q}")
    return JSONResponse(data)


@router.get("/sku-graph")
async def sku_graph(request: Request, sku: str):
    """The neighbourhood /diagnose reasoned over, as nodes and edges (proxies the bot).

    /diagnose returns a conclusion; this returns the evidence behind it, so a disagreement between the
    graph and the card engine is inspectable rather than arguable. Tenant comes from the session, never
    the query string — the bot defaults to its configured tenant and must not be steerable."""
    require_tenant(request)
    q = urllib.parse.quote((sku or "").strip())
    data = await asyncio.to_thread(_bot_get, f"/v1/sku-graph?sku={q}")
    return JSONResponse(data)


@router.get("/ad-budget-plan")
async def ad_budget_plan(request: Request, alpha: float = 0.90, budget: float | None = None,
                         distrust: bool = True):
    """CVaR reallocation of the CURRENT ad budget (#6). Gated as described in the module docstring:
    fails CLOSED, and `caveats` travels with every response, success or failure."""
    from .helpers import ads_preview_allowed

    uid, tid = current(request)
    if not tid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    if not ads_preview_allowed(tid):
        return JSONResponse({"ok": False, "error": "not available"}, status_code=404)
    q = urllib.parse.urlencode({"alpha": alpha, "distrust": str(bool(distrust)).lower(),
                                **({"budget": budget} if budget else {})})
    data = await asyncio.to_thread(_bot_get, f"/v1/ad-budget-plan?{q}")
    return JSONResponse(data)
