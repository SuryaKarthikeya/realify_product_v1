"""Ask API — the conversational home (agent-shaped; stub model behind a swappable narrator).

  POST /api/ask                      — one turn, streamed as Server-Sent Events (meta→deltas→parts→usage→done)
  GET  /api/ask/categories           — the 5 category chips + their seed questions
  GET  /api/ask/models               — model picker registry + current usage
  GET  /api/ask/usage                — monthly usage (overall % + per-model), for the text-box outline bar
  GET  /api/ask/conversations        — History tab: the user's recent conversations
  GET  /api/ask/conversations/{id}   — full transcript (with structured parts)
  POST /api/ask/feedback             — good/bad thumbs on a response
  POST /api/ask/followup             — mark a response into the Follow-ups pane
  GET  /api/ask/followups            — the Follow-ups pane contents

Tenant + user are resolved server-side (never from the client). No model runs here — the narrator seam
(realify.ask.narrator) is the single swap point for the future self-hosted model.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from realify import db
from realify.repositories.ask_repo import AskRepository
from realify.ask import service, models as ask_models, tools as ask_tools
from .deps import require_tenant, current

router = APIRouter()

_SSE_HEADERS = {"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}


async def _body(request):
    try:
        return await request.json()
    except Exception:
        return {}


@router.post("/ask")
async def ask(request: Request):
    tid = require_tenant(request)
    uid, _ = current(request)
    b = await _body(request)
    message = (b.get("message") or "").strip()
    category = b.get("category")
    # a seed-question click may send (category, question_id) instead of raw text
    if not message and category is not None and b.get("question_id") is not None:
        qs = ask_tools.CATEGORY_QUESTIONS.get(category, [])
        qi = b.get("question_id")
        if isinstance(qi, int) and 0 <= qi < len(qs):
            message = qs[qi]
    if not message:
        return JSONResponse({"ok": False, "error": "Ask a question to get started."}, status_code=400)

    if service.at_cap(tid):
        return StreamingResponse(service.limit_frames(tid), media_type="text/event-stream",
                                 headers=_SSE_HEADERS)
    # run_stream relays a live agent's work as it happens and falls back to the compute-then-replay
    # path for non-streaming providers. Sync generator on purpose: Starlette iterates it in a
    # threadpool, so a long model turn never blocks the event loop.
    return StreamingResponse(
        service.run_stream(tid, uid, b.get("conversation_id"), message,
                           model_id=b.get("model_id"), category=category),
        media_type="text/event-stream", headers=_SSE_HEADERS)


@router.get("/ask/categories")
def ask_categories(request: Request):
    require_tenant(request)
    cats = [{"id": cid, "label": ask_tools.CATEGORY_LABEL[cid], "questions": qs}
            for cid, qs in ask_tools.CATEGORY_QUESTIONS.items()]
    return JSONResponse({"ok": True, "categories": cats})


@router.get("/ask/models")
def ask_models_list(request: Request):
    tid = require_tenant(request)
    return JSONResponse({"ok": True, "models": ask_models.MODELS,
                         "default": ask_models.default_model_id(), "usage": service.usage_view(tid)})


@router.get("/ask/usage")
def ask_usage(request: Request):
    tid = require_tenant(request)
    return JSONResponse({"ok": True, "usage": service.usage_view(tid)})


@router.get("/ask/conversations")
def ask_conversations(request: Request):
    tid = require_tenant(request)
    uid, _ = current(request)
    with db.connect() as con:
        rows = AskRepository(con).conversations(tid, uid)
    return JSONResponse({"ok": True, "conversations": rows})


@router.get("/ask/conversations/{conversation_id}")
def ask_conversation(request: Request, conversation_id: str):
    tid = require_tenant(request)
    with db.connect() as con:
        repo = AskRepository(con)
        conv = repo.conversation(tid, conversation_id)
        if not conv:
            return JSONResponse({"ok": False, "error": "Conversation not found."}, status_code=404)
        msgs = repo.messages(tid, conversation_id)
    return JSONResponse({"ok": True, "conversation": conv, "messages": msgs})


@router.delete("/ask/conversations/{conversation_id}")
def ask_conversation_delete(request: Request, conversation_id: str):
    tid = require_tenant(request)
    with db.connect() as con:
        repo = AskRepository(con)
        if not repo.conversation(tid, conversation_id):      # tenant-scoped existence check
            return JSONResponse({"ok": False, "error": "Conversation not found."}, status_code=404)
        repo.delete_conversation(tid, conversation_id)
        con.commit()
    return JSONResponse({"ok": True})


@router.post("/ask/conversations/{conversation_id}/rename")
async def ask_conversation_rename(request: Request, conversation_id: str):
    tid = require_tenant(request)
    b = await _body(request)
    title = (b.get("title") or "").strip()[:120]
    if not title:
        return JSONResponse({"ok": False, "error": "A title is required."}, status_code=400)
    with db.connect() as con:
        repo = AskRepository(con)
        if not repo.conversation(tid, conversation_id):
            return JSONResponse({"ok": False, "error": "Conversation not found."}, status_code=404)
        repo.rename_conversation(tid, conversation_id, title)
        con.commit()
    return JSONResponse({"ok": True, "title": title})


@router.post("/ask/feedback")
async def ask_feedback(request: Request):
    tid = require_tenant(request)
    b = await _body(request)
    mid, rating = b.get("message_id"), b.get("rating")
    if not mid or rating not in ("good", "bad"):
        return JSONResponse({"ok": False, "error": "message_id and rating ('good'|'bad') are required."},
                            status_code=400)
    with db.connect() as con:
        AskRepository(con).set_feedback(tid, mid, rating)
        con.commit()
    return JSONResponse({"ok": True})


@router.post("/ask/followup")
async def ask_followup(request: Request):
    tid = require_tenant(request)
    uid, _ = current(request)
    b = await _body(request)
    mid = b.get("message_id")
    if not mid:
        return JSONResponse({"ok": False, "error": "message_id is required."}, status_code=400)
    with db.connect() as con:
        fid = AskRepository(con).add_followup(tid, uid, b.get("conversation_id"), mid,
                                              (b.get("snippet") or "")[:400])
        con.commit()
    return JSONResponse({"ok": True, "followup_id": fid})


@router.get("/ask/followups")
def ask_followups(request: Request):
    tid = require_tenant(request)
    status = request.query_params.get("status", "open")
    with db.connect() as con:
        rows = AskRepository(con).followups(tid, status=(None if status == "all" else status))
    return JSONResponse({"ok": True, "followups": rows})
