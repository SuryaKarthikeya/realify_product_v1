"""Shared warm design-system component sheet (R11) — the mockup's component classes lifted from
docs/mockups/realify-hub-reimagined.html, centralized so the tester hub (hub.py), the agency FLEET
GRID (h7), the SCOPE-SWITCHER drill-in (h8), and the reskinned agency surfaces all render from ONE
source instead of hand-rolling per-surface CSS. Values match tokens.py (terracotta #C4785B, ink
#1A1A1A, sage #7A9E7E, 9px/14px radii). tokens.py stays the marketing :root source (NOT re-extracted);
this is the reusable component layer on top of it.

- CSS         : the exact mockup stylesheet (hub.py imports this; the hub stays byte-identical).
- AGENCY_CSS  : CSS + fleet-grid / scope-switcher / decisions-panel additions (h7/h8).
- frame(...)  : the SANDBOX frame wrapper (sandbar + pad) used by the hub and agency surfaces.
"""

# ---- mockup <style> block, lifted verbatim (source of truth: realify-hub-reimagined.html <style>) ----
CSS = """
:root{--ink:#1A1A1A;--paper:#F4F0E8;--card:#FFFFFF;--panel2:#FBF9F4;--terra:#C4785B;--terra-d:#A9603F;
--slate:#5B7B94;--sage:#7A9E7E;--gold:#B98A2E;--line:#E1D9CB;--line2:#EDE7DA;--mut:#6E675C;--faint:#9A9182;
--sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Roboto,sans-serif;--mono:ui-monospace,'SF Mono',Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:#E9E3D8;color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55}
#stage{max-width:1120px;margin:0 auto;padding:24px 30px 70px}
.frame{background:var(--paper);border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 2px 6px rgba(26,26,26,.07),0 16px 44px rgba(26,26,26,.09)}
.sandbar{background:repeating-linear-gradient(-45deg,#F3E2C6,#F3E2C6 12px,#EED7B2 12px,#EED7B2 24px);border-bottom:1px solid #DDC391;padding:8px 20px;font-size:12px;color:#6B5320;display:flex;justify-content:space-between;align-items:center}
.sandbar b{font-family:var(--mono);letter-spacing:.08em}
.pad{padding:26px 30px}
.htitle{font-size:23px;font-weight:700;letter-spacing:-.01em;margin:0}
.hsub{color:var(--mut);font-size:13.5px;margin:4px 0 0}
.ordertoggle{display:inline-flex;background:var(--line2);border-radius:100px;padding:3px;margin:18px 0 6px;font-size:12.5px}
.ordertoggle span{padding:6px 14px;border-radius:100px;cursor:pointer;color:var(--mut)}
.ordertoggle span.on{background:var(--ink);color:#fff;font-weight:600}
.step{background:var(--card);border:1px solid var(--line);border-radius:14px;margin-top:16px;overflow:hidden}
.step.locked{opacity:.55}
.step-h{display:flex;align-items:center;gap:12px;padding:16px 20px;border-bottom:1px solid var(--line2);background:var(--panel2)}
.step-n{width:26px;height:26px;border-radius:50%;background:var(--ink);color:#fff;font-family:var(--mono);font-size:13px;font-weight:600;text-align:center;line-height:26px;flex-shrink:0}
.step.done .step-n{background:var(--sage)}.step.locked .step-n{background:var(--faint)}
.step-h h3{margin:0;font-size:15px}.step-h .st-note{margin-left:auto;font-size:12px;color:var(--mut);font-family:var(--mono)}
.step-body{padding:20px}
.subtabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.subtab{border:1px solid var(--line);border-radius:100px;padding:7px 15px;font-size:13px;cursor:pointer;background:#fff}
.subtab.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.field{margin-bottom:14px}.field label{display:block;font-size:12.5px;font-weight:600;margin-bottom:6px}
.field input[type=text],.field input[type=email],.field input[type=number],.field select{width:100%;border:1.5px solid var(--line);border-radius:9px;padding:10px 12px;font-size:14px;font-family:var(--sans);background:#fff;color:var(--ink)}
.field .hint{font-size:11.5px;color:var(--mut);margin-top:4px}
.cols2{display:grid;grid-template-columns:1fr 1fr;gap:0 18px}.cols3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0 16px}
.chips{display:flex;flex-wrap:wrap;gap:7px}
.chip{border:1.5px solid var(--line);border-radius:100px;padding:6px 13px;font-size:13px;cursor:pointer;background:#fff;user-select:none}
.chip.sel{background:var(--ink);color:#fff;border-color:var(--ink)}
.rangewrap{display:flex;align-items:center;gap:14px}.rangewrap input[type=range]{flex:1}
.rangeval{font-family:var(--mono);font-size:18px;font-weight:600;min-width:70px;text-align:right}
.btn{display:inline-block;border-radius:9px;padding:11px 22px;font-size:14px;font-weight:600;cursor:pointer;border:none;font-family:var(--sans)}
.btn.p{background:var(--terra);color:#fff}.btn.p:hover{background:var(--terra-d)}
.btn.g{background:#fff;border:1.5px solid var(--line);color:var(--ink)}.btn.dark{background:var(--ink);color:#fff}
.btn.sm{padding:7px 14px;font-size:12.5px;border-radius:8px}.btn:disabled{opacity:.4;cursor:not-allowed}
.seedrow{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--line2);font-size:13.5px}
.seedrow:last-child{border-bottom:none}.seedrow .meta{color:var(--mut);font-size:12px}
.tag{display:inline-block;font-family:var(--mono);font-size:10px;letter-spacing:.06em;border-radius:100px;padding:2px 9px;background:#EAF0F5;color:var(--slate);margin-left:8px}
.tag.live{background:#EDF3EC;color:#4E7A52}
.roles{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.role{border:1.5px solid var(--line);border-radius:13px;padding:18px;background:#fff}
.role.dis{opacity:.5}
.role .r-role{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--terra);margin-bottom:6px}
.role h4{margin:0 0 4px;font-size:16px}.role p{margin:0 0 12px;font-size:12.5px;color:var(--mut)}
.role .pick{margin-bottom:10px}
.role .pick label{font-size:11px;color:var(--mut);display:block;margin-bottom:3px;font-family:var(--mono);letter-spacing:.04em;text-transform:uppercase}
.role .pick select{width:100%;border:1.5px solid var(--line);border-radius:8px;padding:8px 10px;font-size:13px;background:#fff}
.settingbar{display:flex;align-items:center;gap:14px;background:#EEF0F3;border:1px solid #D8DEE4;border-radius:10px;padding:12px 16px;margin-top:16px;font-size:13px}
.toggle{width:40px;height:23px;border-radius:100px;background:var(--terra);position:relative;cursor:pointer;flex-shrink:0}
.toggle::after{content:"";position:absolute;top:2px;right:2px;width:19px;height:19px;border-radius:50%;background:#fff}
.toggle.off{background:#C4BCB0}.toggle.off::after{right:auto;left:2px}
.emptyhead{background:#FBF7EF;border:1px dashed var(--terra);border-radius:10px;padding:12px 14px;font-size:13px;color:#7A5A47;margin:10px 0}
.shead{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:10px 0}
.shead .cell{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.shead .k{font-family:var(--mono);font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
.shead .v{font-size:13.5px;font-weight:600;margin-top:5px;word-break:break-word}
.note-s{font-size:12px;color:var(--mut)}
details.op{margin-top:18px;background:#FBF3F1;border:1px solid #B3402E33;border-radius:12px;padding:12px 16px}
details.op summary{cursor:pointer;font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#6B6459}
details.op label{display:block;font-size:12px;font-weight:600;margin:12px 0 4px}
details.op input{width:100%;border:1.5px solid var(--line);border-radius:9px;padding:9px 12px}
.stepper{display:flex;gap:6px;margin:12px 0}.stp{flex:1;text-align:center;font-size:11px;padding:7px 4px;border-radius:8px;background:var(--line2);color:var(--mut)}
.stp.on{background:var(--ink);color:#fff;font-weight:600}.stp.done{background:#E8DFD0;color:#6B5B3E}
.stepbody{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:12px 14px;font-size:13.5px;min-height:38px}
"""

# ---- h7 fleet grid + h8 scope-switcher + per-brand decisions additions (agency surfaces only) ----
AGENCY_CSS = CSS + """
.fleet{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
.fleet .role{cursor:pointer;transition:box-shadow .12s}
.fleet .role:hover{box-shadow:0 2px 6px rgba(26,26,26,.08),0 10px 26px rgba(26,26,26,.10)}
.fleet .role.hb-sage{border-left:4px solid var(--sage)}
.fleet .role.hb-gold{border-left:4px solid var(--gold)}
.fleet .role.hb-terra{border-left:4px solid var(--terra)}
.fleet .role .r-role.c-sage{color:var(--sage)}.fleet .role .r-role.c-gold{color:var(--gold)}.fleet .role .r-role.c-terra{color:var(--terra)}
.fleet .role .money{font-family:var(--mono);font-size:12px;color:var(--mut)}
.fleet .role .stake{font-family:var(--mono);font-size:13.5px;font-weight:700;color:var(--ink);margin-top:6px}
.fleethead{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.fleethead .filters{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}
.lenstabs{display:flex;gap:6px;border-bottom:1px solid var(--line);margin-bottom:18px;flex-wrap:wrap}
.lenstab{border:1px solid var(--line);border-bottom:none;border-radius:9px 9px 0 0;padding:8px 14px;font-size:13px;background:#fff;cursor:pointer}
.lenstab.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.lenstab.locked{opacity:.5;cursor:not-allowed}
.dpanel{border:1px solid var(--line);border-radius:12px;background:#fff;overflow:hidden}
.drow{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 16px;border-bottom:1px solid var(--line2)}
.drow:last-child{border-bottom:none}
.drow .sig{font-size:13.5px}.drow .sig .lens{font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--terra)}
.drow .amt{font-family:var(--mono);font-size:13px;font-weight:700;text-align:right;white-space:nowrap}
.locknote{background:#FBF3F1;border:1px solid #B3402E33;border-radius:10px;padding:10px 14px;font-size:12.5px;color:#7A5A47;margin-bottom:14px}
"""


def frame(inner, sandbar_left="<b>SANDBOX</b> · synthetic data · writes go to mock marketplaces",
          sandbar_right="env: staging", backbar_html=""):
    """The SANDBOX frame wrapper: optional back/scope bar, the diagonal sandbar, then a padded body."""
    return (f'{backbar_html}<div class=frame>'
            f'<div class=sandbar><span>{sandbar_left}</span><span>{sandbar_right}</span></div>'
            f'<div class=pad>{inner}</div></div>')


def doc(title, body_css, inner_html, extra_head=""):
    """A full warm-system HTML document (noindex) — <head> wired to AGENCY_CSS, body = #stage frame."""
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8><link rel='icon' type='image/png' href='/assets/Final-logo-VF-white-3.png'>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<meta name=robots content='noindex, nofollow'><title>{title}</title>"
            f"<style>{body_css}</style>{extra_head}</head><body><div id=stage>{inner_html}</div></body></html>")
