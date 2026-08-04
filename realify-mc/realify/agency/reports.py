"""White-label report generator + FACTUALITY GATE (agency-plan P6). Narrative templates interpolate
ONLY engine figures via {{key}} placeholders. The gate then extracts every numeric token from the
rendered narrative, normalizes it (strips $/₹/%/commas), and asserts each is one the renderer actually
emitted from the engine JSON. Any number that isn't (a literal snuck into the template) BLOCKS the
report — the gate is enforcement, not logging. White-label styling (logo/colors) wraps the narrative
and is NOT part of the gated text."""
import re

_TOKEN = re.compile(r"[₹$]?\s?\d[\d,]*\.?\d*\s?%?")


class FactualityError(Exception):
    """Raised when the rendered report contains a numeric claim not backed by the engine JSON."""


def _norm(tok):
    return re.sub(r"[^\d.]", "", tok).rstrip(".")


def render_narrative(template, figures):
    """Substitute {{key}} with figures[key] (a preformatted string). Returns (text, emitted_norms)."""
    emitted = set()

    def repl(m):
        val = str(figures[m.group(1)])
        n = _norm(val)
        if n:
            emitted.add(n)
        return val

    return re.sub(r"\{\{(\w+)\}\}", repl, template), emitted


def numeric_tokens(text):
    return [t for t in _TOKEN.findall(text) if _norm(t)]


def factuality_check(rendered, emitted):
    for tok in numeric_tokens(rendered):
        if _norm(tok) not in emitted:
            return {"ok": False, "offending": tok.strip()}
    return {"ok": True}


def generate(template, figures, white_label=None):
    """Render + gate. Returns the report HTML, or raises FactualityError (BLOCKED, never sent)."""
    narrative, emitted = render_narrative(template, figures)
    gate = factuality_check(narrative, emitted)
    if not gate["ok"]:
        raise FactualityError(f"factuality gate BLOCKED report: unverified figure {gate['offending']!r}")
    wl = white_label or {}
    header = (f"<header style='color:{wl.get('color', '#111')}'>{wl.get('logo', '')}"
              f"{wl.get('agency_name', '')}</header>") if wl else ""
    return header + "<section>" + narrative + "</section>"
