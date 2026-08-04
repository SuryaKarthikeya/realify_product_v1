"""Bridge to the live RIA agent (realify-bots) — the real brain behind the Ask surface.

The bot at `/v1/chat` runs the agent loop: it writes SQL against the seller's real data
(`query_cdp`), may chain predictive tools (`forecast_demand`, `optimize_price`), then gates every
number in its draft against the tool results before releasing the answer. It streams
newline-delimited JSON. This module is the only place that vocabulary is understood: it translates
the bot's frames into the neutral events the Ask service turns into SSE.

Stdlib-only (urllib), same as routers/assistant.py — realify-mc gains no dependency. Callers are
SYNC generators on purpose: Starlette iterates a sync StreamingResponse body in a threadpool, so a
30-second model turn never blocks the event loop.

Bot frame -> normalized event:
  {"status": "..."}                          -> {"kind":"status","text":...}
  {"chatId": "..."}                          -> {"kind":"chat_id","chat_id":...}
  {"debug":{"tool":"gemma-0","content":{...}}} -> {"kind":"tool", name/sql/row_count/ok/...}
  {"type":"stream","data":"..."}             -> {"kind":"text","text":...}
  {"debug":{"tool":"grounding",...}}         -> {"kind":"grounding", pct/grounded/n_numbers}
  {"debug":{"tool":"decision_record",...}}   -> {"kind":"decision", tier/label/tools}
  {"error": "..."}                           -> {"kind":"error","message":...}
"""
import json
import os
import urllib.error
import urllib.request

# The running RIA bot, and the seller identity injected server-side (never from the client) — the
# same convention routers/assistant.py uses for the legacy chat widget.
BOT_URL = os.environ.get("RIA_BOT_URL", "http://localhost:8090").rstrip("/")
DEMO_SELLER = os.environ.get("RIA_DEMO_SELLER", "A1REALIFY001")
TIMEOUT = int(os.environ.get("RIA_BOT_TIMEOUT", "180"))

# Tool name -> how we describe it to the seller. `query_cdp` is a trained token in the model's
# vocabulary (it predates the realify_mc move); it runs SQL against the seller's data.
TOOL_LABEL = {
    "query_cdp": "Queried your data",
    "query_graph": "Traversed your signal graph",
    "forecast_demand": "Forecast demand",
    "optimize_price": "Ran price optimization",
    "diagnose_sku": "Diagnosed the SKU",
}


def available():
    """Cheap liveness probe so the narrator can fall back to the stub without a 180s hang."""
    try:
        req = urllib.request.Request(f"{BOT_URL}/", method="GET")
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def _tool_event(tool, content):
    """Normalize one `debug` frame. Returns an event dict, or None if it carries nothing useful."""
    if not isinstance(content, dict):
        return None

    # grounding gate: how many figures in the answer were traceable to tool output
    if "grounding" in content:
        g = content["grounding"] or {}
        return {"kind": "grounding", "ok": bool(g.get("ok")), "pct": g.get("pct"),
                "grounded": g.get("grounded"), "n_numbers": g.get("n_numbers"),
                "ungrounded": g.get("ungrounded") or []}

    # decision record: the confidence tier the answer earned + which tools produced it
    if "decision_record" in content:
        dr = content["decision_record"] or {}
        conf = dr.get("confidence") or {}
        return {"kind": "decision", "tier": conf.get("tier"), "label": conf.get("label"),
                "note": conf.get("note") or "", "tools": dr.get("tools") or []}

    # a tool call: `content` carries the tool name plus its own shape (sql/row_count for query_cdp,
    # accuracy/explanation for the predictive tools)
    name = content.get("tool")
    if not name:
        return None
    ev = {"kind": "tool", "name": name, "label": TOOL_LABEL.get(name, name.replace("_", " ").title()),
          "ok": content.get("ok", True)}
    for k in ("sql", "row_count", "error", "explanation", "accuracy", "backend", "sku"):
        if content.get(k) is not None:
            ev[k] = content[k]
    return ev


def stream_turn(question, parent_chat_id=None, channel="chat"):
    """Run one agent turn against the bot, yielding normalized events as they arrive.

    Never raises: transport failures surface as a single {"kind":"error"} event so the caller can
    fall back to the deterministic narrator rather than losing the turn.
    """
    body = {"question": question}
    if parent_chat_id:
        body["parentChatId"] = parent_chat_id
    req = urllib.request.Request(
        f"{BOT_URL}/v1/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "ic": DEMO_SELLER, "channel": channel},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            for raw in resp:                       # bot streams newline-delimited JSON
                line = (raw or b"").decode("utf-8", "replace").strip()
                if not line:
                    continue
                try:
                    f = json.loads(line)
                except Exception:
                    continue
                if not isinstance(f, dict):
                    continue

                if f.get("error"):
                    yield {"kind": "error", "message": str(f["error"])}
                elif f.get("chatId"):
                    yield {"kind": "chat_id", "chat_id": f["chatId"]}
                elif f.get("type") == "stream":
                    txt = f.get("data") or ""
                    if txt:
                        yield {"kind": "text", "text": txt}
                elif "status" in f:
                    # the bot emits a trailing empty status to clear the indicator — drop it
                    if (f.get("status") or "").strip():
                        yield {"kind": "status", "text": f["status"]}
                elif isinstance(f.get("debug"), dict):
                    ev = _tool_event(f["debug"].get("tool"), f["debug"].get("content"))
                    if ev:
                        yield ev
    except urllib.error.URLError as e:
        yield {"kind": "error", "message": f"RIA is unavailable ({e.reason})."}
    except Exception as e:                          # noqa: BLE001 — a dead bot must not kill the turn
        yield {"kind": "error", "message": f"RIA error: {e}"}
