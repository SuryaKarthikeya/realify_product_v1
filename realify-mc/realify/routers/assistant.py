"""RIA assistant proxy — same-origin bridge from the dashboard to the RIA bot.

The floating chat widget in frontend.html POSTs here (same origin, so the session
cookie rides along). We resolve the logged-in tenant from the session, inject the
seller identity server-side, and stream the bot's newline-delimited JSON straight
back to the browser. Keeping this same-origin avoids CORS and keeps the bot's
identity header off the client.

Stdlib-only (urllib) so realify-mc gains no new dependency.
"""
import os, json, urllib.request, urllib.error
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from .deps import current

router = APIRouter()

# The running RIA bot and the seller we demo as. Tenant 14 (Realify) is seeded in
# both the insight feed and the margin engine; A1REALIFY001 is that seller's id.
BOT_URL = os.environ.get("RIA_BOT_URL", "http://localhost:8090").rstrip("/")
DEMO_SELLER = os.environ.get("RIA_DEMO_SELLER", "A1REALIFY001")


@router.post("/assistant/chat")
async def assistant_chat(request: Request):
    uid, tid = current(request)
    if not tid:
        return JSONResponse({"error": "Please sign in to use the assistant."}, status_code=401)

    body = await request.body()

    def stream():
        req = urllib.request.Request(
            f"{BOT_URL}/v1/chat",
            data=body or b"{}",
            headers={
                "Content-Type": "application/json",
                "ic": DEMO_SELLER,           # seller identity, injected server-side
                "channel": "chat",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                for line in resp:            # bot streams newline-delimited JSON
                    if line:
                        yield line
        except urllib.error.URLError as e:
            yield (json.dumps({"error": f"RIA is unavailable ({e.reason})."}) + "\n").encode()
        except Exception as e:               # noqa: BLE001 - surface any failure to the widget
            yield (json.dumps({"error": f"Assistant error: {e}"}) + "\n").encode()

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
