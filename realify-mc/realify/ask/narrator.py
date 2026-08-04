"""The narrator seam — the ONE place a model lives.

`Narrator.compose(question, facts, context, history) -> {"content", "parts"}` is the whole contract.
Today `StubNarrator` composes a data-grounded answer from the tool facts (no LLM). Tomorrow a
`SelfHostedNarrator` (Realify hosts its own model) implements the same method by POSTing
{system, history, question, tool_facts} to an inference endpoint and mapping the reply into the same
{content, parts} shape — the service, router, persistence and UI don't change. `get_narrator(model)`
dispatches on the model's `provider`.

Parts vocabulary (rendered by the Ask UI, and attachable to feedback/follow-ups):
  {"type":"text","text":str}                          — prose (the service streams this as deltas)
  {"type":"tiles","tiles":[{label,value,tone}]}       — metric tiles (V4 look)
  {"type":"citations","items":[{finding,exposure_val,severity,asin,card_id,surface}]}
  {"type":"actions","actions":[{label,surface,card_id}]}
  {"type":"followups","questions":[str,...]}
  {"type":"tool","calls":[{label,name,sql,row_count,...}],"statuses":[str,...]}   — RiaNarrator only
  {"type":"confidence","tier","label","grounded_pct","tools":[str,...]}           — RiaNarrator only
  {"type":"_ria","chat_id":str}                       — internal: chains the next turn's context

Unknown part types are ignored by the UI, so a narrator may add its own without a frontend change.
"""
from . import tools as _tools


class Narrator:
    """Protocol. A provider implements compose() and returns {'content': str, 'parts': list}."""

    def compose(self, question, facts, context, history):
        raise NotImplementedError


class StubNarrator(Narrator):
    """Deterministic, data-grounded stub — reads like the real thing because it cites the tenant's actual
    signals. Replaceable by a hosted model behind the same contract."""

    def compose(self, question, facts, context, history):
        sym = (context or {}).get("symbol", "₹")
        label = facts.get("label", "your business")
        count = facts.get("count", 0)
        items = facts.get("items", [])

        parts = []

        # 1) No connected data yet → honest, actionable empty (never invent numbers).
        if not (context or {}).get("provisioned") and (context or {}).get("sku_count", 0) == 0:
            content = ("I don't see any connected data for this account yet, so I can't ground an answer. "
                       "Connect your reports and I'll answer this from your real numbers.")
            parts.append({"type": "text", "text": content})
            parts.append({"type": "actions",
                          "actions": [{"label": "Connect your data", "surface": "onboarding",
                                       "card_id": None}]})
            return {"content": content, "parts": parts}

        # 2) Nothing in this area right now → clear all-clear.
        if count == 0:
            content = (f"Good news — nothing in {label.lower()} needs your attention right now. "
                       "I checked your live signals and found no open issues in this area.")
            parts.append({"type": "text", "text": content})
            parts.append({"type": "followups", "questions": self._suggest(facts)})
            return {"content": content, "parts": parts}

        # 3) Grounded summary of the real signals.
        lead = items[0]
        urgent = facts.get("urgent", 0)
        opener = (f"Here's what stands out in {label.lower()}: I found "
                  f"{count} signal{'' if count == 1 else 's'}")
        opener += f", {urgent} needing attention now. " if urgent else ". "
        body = ""
        if lead.get("finding"):
            money = f" (~{lead['exposure_val']})" if lead.get("exposure_val") else ""
            body = f"Top of the list: {self._strip(lead['finding'])}{money}. "
        rest = [self._strip(i["finding"]) for i in items[1:3] if i.get("finding")]
        if rest:
            body += "Also worth a look: " + "; ".join(rest) + "."
        content = (opener + body).strip()

        parts.append({"type": "text", "text": content})
        if facts.get("tiles"):
            parts.append({"type": "tiles", "tiles": facts["tiles"]})
        if items:
            parts.append({"type": "citations",
                          "items": [{"finding": self._strip(i.get("finding") or ""),
                                     "exposure_val": i.get("exposure_val"),
                                     "severity": i.get("severity"),
                                     "asin": i.get("asin"),
                                     "card_id": i.get("card_id"),
                                     "surface": i.get("surface")} for i in items]})
        if facts.get("actions"):
            parts.append({"type": "actions", "actions": facts["actions"]})
        parts.append({"type": "followups", "questions": self._suggest(facts)})
        return {"content": content, "parts": parts}

    @staticmethod
    def _strip(s):
        import re
        return re.sub(r"<[^>]+>", "", s or "").strip().rstrip(".")

    @staticmethod
    def _suggest(facts):
        cat = facts.get("category")
        qs = _tools.CATEGORY_QUESTIONS.get(cat, [])
        return qs[1:4] if qs else []


class SelfHostedNarrator(Narrator):
    """Placeholder for the future Realify-hosted model. Wire an HTTP call to the inference endpoint here;
    map its reply into {content, parts}. Not configured yet → falls back to the stub so the surface still
    works end to end."""

    def __init__(self, model):
        self.model = model

    def compose(self, question, facts, context, history):
        # TODO: POST {system, history, question, tool_facts} to the self-hosted endpoint; map reply.
        return StubNarrator().compose(question, facts, context, history)


class RiaNarrator(Narrator):
    """The live RIA agent (realify-bots): it writes its own SQL against the seller's data and gates
    every number in the answer against the tool results.

    Unlike the stub, this narrator does not receive pre-gathered `facts` — the agent chooses and runs
    its own tools, so the tool layer is bypassed and the trace it produces IS the evidence. It emits
    two part types the stub never does:
      {"type":"tool","calls":[{label,name,sql,row_count,...}],"statuses":[str,...]}
      {"type":"confidence","tier":str,"label":str,"grounded_pct":num,"tools":[str,...]}

    `stream()` is the primary entry point (the service replays it live). `compose()` drains the same
    stream for callers that want the finished turn, and both degrade to the deterministic stub when
    the bot is unreachable — a dead bot must never lose the seller's question.
    """

    def __init__(self, model=None):
        self.model = model or {}

    # ---- streaming (primary) ----
    def stream(self, question, context, history, parent_chat_id=None):
        """Yield normalized agent events, then a final {"kind":"done","content","parts"}.

        Falls back to the stub (as a single text event + done) if the agent produced no prose.
        """
        from . import ria

        text_parts, statuses, calls = [], [], []
        grounding, decision, chat_id, error = None, None, None, None

        for ev in ria.stream_turn(question, parent_chat_id=parent_chat_id):
            kind = ev.get("kind")
            if kind == "text":
                text_parts.append(ev["text"])
                yield ev
            elif kind == "status":
                statuses.append(ev["text"])
                yield ev
            elif kind == "tool":
                calls.append({k: v for k, v in ev.items() if k != "kind"})
                yield ev
            elif kind == "grounding":
                grounding = ev
            elif kind == "decision":
                decision = ev
                yield ev
            elif kind == "chat_id":
                chat_id = ev.get("chat_id")
            elif kind == "error":
                error = ev.get("message")

        content = "".join(text_parts).strip()
        if not content:
            # The agent gave us nothing usable (bot down, or it errored mid-turn). Degrade to the
            # deterministic narrator over the tenant's REAL signals — and ALWAYS say the live analyst
            # didn't run. Silence here would be dishonest: the stub's "nothing needs your attention"
            # would read as an all-clear when the truth is we never reached the agent.
            facts = _empty_facts()
            try:
                cat = _tools.route_category(question)
                facts = _tools.gather((context or {}).get("tenant_id"), category=cat, question=question)
            except Exception:
                pass
            stub = StubNarrator().compose(question, facts, context, history)
            note = ("**The live analyst didn't answer** — "
                    f"{_short_reason(error)} Here's what your signal engine shows instead:\n\n"
                    + stub["content"])
            parts = [p for p in stub["parts"] if p.get("type") != "text"]
            parts.insert(0, {"type": "text", "text": note})
            yield {"kind": "text", "text": note}
            yield {"kind": "done", "content": note, "parts": parts, "chat_id": chat_id,
                   "degraded": True}
            return

        parts = [{"type": "text", "text": content}]
        if calls or statuses:
            parts.append({"type": "tool", "calls": calls, "statuses": statuses})
        conf = _confidence_part(grounding, decision)
        if conf:
            parts.append(conf)
        # the agent doesn't propose follow-ups; offer the category's curated ones when we can route
        qs = _routed_followups(question)
        if qs:
            parts.append({"type": "followups", "questions": qs})

        yield {"kind": "done", "content": content, "parts": parts, "chat_id": chat_id,
               "degraded": False}

    # ---- non-streaming (compatibility with the Narrator protocol) ----
    def compose(self, question, facts, context, history):
        final = {"content": "", "parts": []}
        for ev in self.stream(question, context, history):
            if ev.get("kind") == "done":
                final = {"content": ev["content"], "parts": ev["parts"]}
        return final


def _empty_facts():
    """Facts shape the stub understands, with nothing in it — last-resort degraded path."""
    return {"label": "your business", "count": 0, "items": [], "category": None}


def _short_reason(error):
    """One clause naming why, without leaking a stack trace or an internal host to the seller."""
    e = (error or "").lower()
    if not error:
        return "it returned no answer."
    if "unavailable" in e or "refused" in e or "urlopen" in e or "timed out" in e or "timeout" in e:
        return "it's temporarily unreachable."
    return "it hit an error."


def _confidence_part(grounding, decision):
    """Fold the grounding gate + decision record into one trust badge the UI can render."""
    if not grounding and not decision:
        return None
    p = {"type": "confidence"}
    if decision:
        p["tier"] = decision.get("tier")
        p["label"] = decision.get("label")
        p["tools"] = decision.get("tools") or []
        if decision.get("note"):
            p["note"] = decision["note"]
    if grounding:
        p["grounded_pct"] = grounding.get("pct")
        p["grounded"] = grounding.get("grounded")
        p["n_numbers"] = grounding.get("n_numbers")
    return p


def _routed_followups(question):
    cat = _tools.route_category(question)
    qs = _tools.CATEGORY_QUESTIONS.get(cat, []) if cat else []
    return qs[1:4] if qs else []


def get_narrator(model):
    """Dispatch on provider. Unknown/absent provider → stub (never fail the turn)."""
    provider = (model or {}).get("provider", "stub")
    if provider == "ria":
        return RiaNarrator(model)
    if provider == "self_hosted":
        return SelfHostedNarrator(model)
    return StubNarrator()
