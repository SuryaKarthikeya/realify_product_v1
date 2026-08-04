"""Ask orchestration — runs one turn end to end, then yields SSE frames.

Flow (agent-shaped): resolve model → load/create conversation → persist the user turn → assemble the
context pack → route to the tool layer for REAL facts → narrator composes {content, parts} → persist the
assistant turn → bump usage. Everything is persisted BEFORE streaming, so a client disconnect never loses
the turn. `sse_frames()` then replays the result as `text/event-stream` (meta → deltas → parts → usage →
done), which is exactly the frame sequence a real streaming model will produce.
"""
import datetime
import json
import uuid

from realify import db
from realify.repositories.ask_repo import AskRepository
from . import context as _context, tools as _tools, models as _models, narrator as _narrator


def _title_from(text):
    t = " ".join((text or "").split())
    return (t[:48] + "…") if len(t) > 48 else (t or "New chat")


def at_cap(tenant_id):
    con = db.connect()
    try:
        used = AskRepository(con).usage(tenant_id).get("total", 0)
    finally:
        con.close()
    return used >= _models.MONTHLY_QUERY_CAP


def usage_view(tenant_id):
    con = db.connect()
    try:
        return _models.usage_view(AskRepository(con).usage(tenant_id))
    finally:
        con.close()


def run(tenant_id, user_id, conversation_id, message, model_id=None, category=None):
    """Execute one turn. Returns a result dict (all persistence + usage done). Does NOT enforce the cap —
    the router checks `at_cap` first and streams a limit frame instead of calling this."""
    model = _models.get_model(model_id)
    ctx = _context.build(tenant_id)

    con = db.connect()
    try:
        repo = AskRepository(con)
        new_conversation = not conversation_id or not repo.conversation(tenant_id, conversation_id)
        if new_conversation:
            conversation_id = repo.create_conversation(tenant_id, user_id, model["id"],
                                                        title=_title_from(message))
        history = repo.history_for_model(tenant_id, conversation_id)   # prior turns (before this one)
        repo.add_message(tenant_id, conversation_id, "user", message, model_id=model["id"],
                         category=category)

        facts = _tools.gather(tenant_id, category=category, question=message)
        composed = _narrator.get_narrator(model).compose(message, facts, ctx, history)

        assistant_id = repo.add_message(tenant_id, conversation_id, "assistant",
                                        composed.get("content", ""), parts=composed.get("parts", []),
                                        model_id=model["id"], category=category)
        repo.touch_conversation(tenant_id, conversation_id,
                                title=_title_from(message) if new_conversation else None)
        repo.bump_usage(tenant_id, model["id"])
        con.commit()
    finally:
        con.close()

    return {
        "conversation_id": conversation_id,
        "assistant_message_id": assistant_id,
        "model_id": model["id"],
        "content": composed.get("content", ""),
        "parts": composed.get("parts", []),
        "usage": usage_view(tenant_id),
    }


def _sse(obj):
    return "data: " + json.dumps(obj) + "\n\n"


def _parent_chat_id(messages):
    """The bot's chat id from the last assistant turn, so a follow-up keeps the agent's context.

    Stored as an internal `_ria` part (the UI ignores unknown part types), which avoids a migration
    just to carry one opaque id.
    """
    for m in reversed(messages or []):
        if m.get("role") != "assistant":
            continue
        for p in m.get("parts") or []:
            if p.get("type") == "_ria" and p.get("chat_id"):
                return p["chat_id"]
    return None


def run_stream(tenant_id, user_id, conversation_id, message, model_id=None, category=None):
    """Execute one turn, yielding SSE frames AS THE AGENT WORKS (sync generator — Starlette iterates
    it in a threadpool, so a 30s model turn never blocks the event loop).

    Providers that aren't live (the deterministic stub) have nothing to stream, so they take the
    original compute-then-replay path — identical output, no behaviour change.

    Ordering guarantee: the user's question is persisted BEFORE any model work, and the assistant
    turn is persisted BEFORE the closing frames. A client that disconnects mid-answer still finds the
    full turn in its history.
    """
    model = _models.get_model(model_id)
    if model.get("provider") != "ria":
        result = run(tenant_id, user_id, conversation_id, message, model_id=model_id,
                     category=category)
        yield from sse_frames(result)
        return

    ctx = _context.build(tenant_id)

    # --- open the conversation + persist the question up front ---
    con = db.connect()
    try:
        repo = AskRepository(con)
        new_conversation = not conversation_id or not repo.conversation(tenant_id, conversation_id)
        if new_conversation:
            conversation_id = repo.create_conversation(tenant_id, user_id, model["id"],
                                                       title=_title_from(message))
        prior = repo.messages(tenant_id, conversation_id)
        history = [{"role": m["role"], "content": m["content"] or ""} for m in prior]
        parent = _parent_chat_id(prior)
        repo.add_message(tenant_id, conversation_id, "user", message, model_id=model["id"],
                         category=category)
        con.commit()
    finally:
        con.close()

    assistant_id = uuid.uuid4().hex          # announced now, persisted after the agent finishes
    yield _sse({"type": "meta", "conversation_id": conversation_id, "message_id": assistant_id,
                "model_id": model["id"], "streaming": True})

    # --- run the agent, relaying its work live ---
    narrator = _narrator.get_narrator(model)
    content, parts, chat_id = "", [], None
    try:
        for ev in narrator.stream(message, ctx, history, parent_chat_id=parent):
            kind = ev.get("kind")
            if kind == "status":
                yield _sse({"type": "status", "text": ev.get("text") or ""})
            elif kind == "tool":
                yield _sse({"type": "tool", "call": {k: v for k, v in ev.items() if k != "kind"}})
            elif kind == "text":
                # The agent buffers its answer on purpose (the grounding gate must see the whole
                # draft before any number reaches the seller), so this arrives in few, large chunks.
                # Re-chunk for smooth rendering — the text is already gated, nothing is revealed early.
                for piece in _chunks(ev.get("text") or "", per=6):
                    yield _sse({"type": "delta", "text": piece})
            elif kind == "decision":
                yield _sse({"type": "verdict", "tier": ev.get("tier"), "label": ev.get("label")})
            elif kind == "done":
                content, parts = ev.get("content") or "", list(ev.get("parts") or [])
                chat_id = ev.get("chat_id")
    except Exception:                       # noqa: BLE001 — never strand the turn mid-stream
        pass

    if not content:
        yield _sse({"type": "error", "code": "no_answer",
                    "message": "I couldn't produce a grounded answer for that. Try narrowing it."})
        yield _sse({"type": "usage", "usage": usage_view(tenant_id)})
        yield _sse({"type": "done"})
        return

    if chat_id:                              # carry the agent's thread for the next turn
        parts.append({"type": "_ria", "chat_id": chat_id})

    # --- persist the assistant turn + count usage BEFORE the closing frames ---
    con = db.connect()
    try:
        repo = AskRepository(con)
        repo.add_message(tenant_id, conversation_id, "assistant", content, parts=parts,
                         model_id=model["id"], category=category, message_id=assistant_id)
        repo.touch_conversation(tenant_id, conversation_id,
                                title=_title_from(message) if new_conversation else None)
        repo.bump_usage(tenant_id, model["id"])
        con.commit()
    finally:
        con.close()

    yield _sse({"type": "meta", "conversation_id": conversation_id, "message_id": assistant_id,
                "model_id": model["id"]})
    for part in parts:
        if part.get("type") in ("text", "_ria"):
            continue                         # already streamed / internal
        yield _sse({"type": "part", "part": part})
    yield _sse({"type": "usage", "usage": usage_view(tenant_id)})
    yield _sse({"type": "done"})


def _chunks(text, per=4):
    words = (text or "").split(" ")
    for i in range(0, len(words), per):
        yield (" " if i else "") + " ".join(words[i:i + per])


def sse_frames(result):
    """Yield the turn as SSE frames. Text streams as `delta`s (simulated typing); structured parts other
    than the leading prose are sent as `part` frames; then `usage` and `done`."""
    yield _sse({"type": "meta", "conversation_id": result["conversation_id"],
                "message_id": result["assistant_message_id"], "model_id": result["model_id"]})
    for chunk in _chunks(result.get("content", "")):
        yield _sse({"type": "delta", "text": chunk})
    for part in result.get("parts", []):
        if part.get("type") == "text":
            continue                      # already streamed as deltas
        yield _sse({"type": "part", "part": part})
    yield _sse({"type": "usage", "usage": result.get("usage")})
    yield _sse({"type": "done"})


def limit_frames(tenant_id):
    """Streamed when the tenant is at its monthly cap — no model call, no bump."""
    yield _sse({"type": "meta", "conversation_id": None, "message_id": None})
    yield _sse({"type": "error", "code": "usage_limit",
                "message": f"You've used all {_models.MONTHLY_QUERY_CAP} queries for this month. "
                           "Usage resets at the start of next month."})
    yield _sse({"type": "usage", "usage": usage_view(tenant_id)})
    yield _sse({"type": "done"})
