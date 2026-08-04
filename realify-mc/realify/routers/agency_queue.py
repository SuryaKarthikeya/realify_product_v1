"""R11 Part D — /agency/queue is RETIRED. The cross-brand action stream is gone: the agency now triages
on the FLEET GRID (/agency/console, mockup h7) and ACTS by drilling into a brand (scope-switcher, h8),
where per-brand decisions surface. GET /agency/queue redirects to the fleet grid so any stale link/
bookmark lands somewhere sensible; no UI links to it anymore. The queue's propose/dismiss endpoints
live on in agency_console.py — the drill-in reuses that same envelope-enforced act path."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse

from ..agency.guard import require_agency_console

router = APIRouter()


@router.get("/agency/queue", dependencies=[Depends(require_agency_console)])
def queue_retired(request: Request):
    """Retired in R11 — the cross-brand queue is replaced by the fleet grid + per-brand drill-in."""
    return RedirectResponse("/agency/console", status_code=307)
