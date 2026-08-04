"""Shared design tokens — the single source of the marketing palette + primitives (R10, moved up from
R11 per DESIGN-SYSTEM.md §6). `TOKENS` is ui.py's exact `:root{…}` block, lifted verbatim so marketing
renders pixel-identical; `SHELL_CSS` bundles the reusable primitives (buttons, tags, cards) so the
agency team UI (R10) and later the interior reskin (R13) can import ONE token source instead of
hand-rolling per-surface CSS."""

# The marketing palette. V4 DLS (cool, light-first, all-sans). Token NAMES are unchanged so every
# consumer (ui.py, SHELL_CSS, agency imports) reskins from this one edit. `--blue` is now an actual blue
# accent (was the misnamed terracotta). `--serif` now carries the sans display stack (V4 is all-sans;
# flip this value to a serif stack to give marketing a display face). Keep test_r10_tokens.py in sync.
TOKENS = (
    ':root{--ink:#14161C;--ink2:#3B4250;--muted:#6C7482;--bg:#F4F6F9;--soft:#EEF1F5;--card:#FFFFFF;\n'
    '--line:#E7EAF0;--blue:#2E68E6;--blue-d:#1E52C8;--slate:#5A6475;--green:#12925A;--amber:#B9770A;--red:#D8403A;\n'
    '--serif:system-ui,-apple-system,"Segoe UI",Roboto,Inter,Arial,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,monospace}'
)

# Reusable primitives (button/tag/label/card) for surfaces that import the token source directly.
# These mirror ui.py's classes so an imported surface looks like the marketing system.
SHELL_CSS = TOKENS + """
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif;line-height:1.55;margin:0}
a{color:var(--blue);text-decoration:none}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
.btn{display:inline-block;border:none;border-radius:9px;padding:11px 20px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}
.btn-blue{background:var(--blue);color:#fff}.btn-blue:hover{background:var(--blue-d)}
.btn-ghost{background:transparent;color:var(--ink);border:1.5px solid var(--ink)}
.btn.sm{padding:7px 14px;font-size:12.5px;border-radius:8px}
.btn:disabled{opacity:.45;cursor:not-allowed}
.tag{display:inline-block;font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--blue);background:#EAF1FE;border-radius:20px;padding:5px 12px}
.label{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
h1{font-family:var(--serif);font-size:34px;font-weight:700;letter-spacing:-.015em}
h2{font-family:var(--serif);font-size:24px;font-weight:700;margin:10px 0}
h3{font-family:var(--serif);font-size:18px;font-weight:700}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px}
"""


def state_page(title, message, status_label="Restricted"):
    """A design-system'd empty/unauth state (R9.1 Part D) — not a bare <h1>. Returns full HTML."""
    import html as _h
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8><meta name=robots content='noindex'>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>{_h.escape(title)}</title><style>" + SHELL_CSS +
        "body{display:flex;align-items:center;justify-content:center;min-height:100vh;background:var(--soft)}"
        ".sc{max-width:440px;background:var(--card);border:1px solid var(--line);border-radius:16px;"
        "padding:34px;text-align:center}.sc .k{font-family:var(--mono);font-size:11px;letter-spacing:.14em;"
        "text-transform:uppercase;color:var(--blue)}.sc h1{font-size:24px;margin:10px 0}.sc p{color:var(--ink2);font-size:14px}"
        "</style></head><body><div class=sc>"
        f"<div class=k>{_h.escape(status_label)}</div><h1>{_h.escape(title)}</h1>"
        f"<p>{_h.escape(message)}</p></div></body></html>")
