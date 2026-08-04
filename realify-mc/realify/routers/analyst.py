"""Your Category Analyst — read surface.

An analyst that did the work overnight: a dated memo + a ranked shortlist of moves, scoped to the
tenant and a category/price-band. Synthesis leads; the data threads are drill-down. Tenancy is
resolved server-side via require_tenant() (the client never supplies tenant_id; fail closed). The
payload is produced by the synthesis SEAM in realify.domain.analyst (a typed fixture today).

Mounted at /api (existing UI) AND /api/v1 (frozen contract), like insights/cards/cmaa.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from realify.domain import analyst
from .deps import require_tenant

router = APIRouter()


@router.get("/category-analyst")
def category_analyst(request: Request, category: str = None, price_band: str = None):
    tid = require_tenant(request)                      # server-side tenant scope; 401 if unauthenticated
    brief = analyst.synthesize_category_analyst(tid, category, price_band)
    return JSONResponse(analyst.to_public(brief))
