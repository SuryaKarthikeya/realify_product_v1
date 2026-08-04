"""R11 Part B — the FLEET GRID (mockup h7): the agency's triage home. One card per managed brand with
a health band (sage/gold/terracotta left edge), top signal + top recommended action, and the load-
bearing $-AT-STAKE per brand (cards sort by it — it replaces the retired queue's $-priority triage).
"My book vs All accounts" filter + AM-owner tag. Lifts the mockup's .role/.fleet component CSS via
hubkit (the warm design system), so it renders pixel-close to h7."""
import html as _h

from . import hubkit
from . import backbar as _backbar
from .busy_modal import SNIPPET as _BUSY_MODAL

_HEALTH_LABEL = {"sage": "Healthy", "gold": "Watch", "terra": "At risk"}


def _card(c):
    hb = c["health"]                                          # 'sage' | 'gold' | 'terra'
    name = _h.escape(c["name"])
    # R15.2 Part C — show the per-brand OWNER (varies across the book), not the single all-brands AM.
    owner = _h.escape(c.get("owner_name") or c.get("am_name") or "unassigned")
    label = _HEALTH_LABEL.get(hb, "Healthy")
    signal = _h.escape(c.get("top_signal") or "No open decisions.")
    action = _h.escape(c.get("top_action") or "Nothing to do right now.")
    money = _h.escape(c.get("money_line") or "")
    # R15.2 Part B — $-at-stake in the brand's real currency (localized), never a hardcoded "$".
    stake = _h.escape(c.get("stake_display") or (c.get("symbol") or "$") + "0")
    btn = "btn dark sm" if hb != "terra" else "btn g sm"
    href = f"/agency/brand/{c['tenant_id']}"
    return (f"<div class='role hb-{hb}' onclick=\"location.href='{href}'\">"
            f"<div class='r-role c-{hb}'>{label} · {owner}</div><h4>{name}</h4>"
            f"<p>Top signal: {signal}<br>Next: {action}</p>"
            f"<div class='money'>{money}</div>"
            f"<div class='stake'>{stake} at stake</div>"
            # Open brand → drill in: an unprovisioned brand lands on the onboarding wizard, else the app.
            f"<div style='margin-top:8px'><a class='{btn}' href='{href}'>Open brand →</a></div></div>")


def fleet_html(request, agency_name, cards, book_mode, mine_n, all_n, add_form_html=""):
    """Render the h7 fleet grid. `cards` are already sorted by $-at-stake DESC (paused sink to the end)."""
    need = sum(1 for c in cards if c["health"] == "terra")
    grid = "".join(_card(c) for c in cards) or (
        "<div class='emptyhead'>No client brands yet — add your first client to begin.</div>")
    chip = lambda mode, label: (
        f"<a class='chip{' sel' if book_mode==mode else ''}' "
        f"href='/agency/console?book={mode}' style='text-decoration:none'>{label}</a>")
    inner = (
        "<div class=fleethead>"
        "<h2 class=htitle>Fleet</h2>"
        f"<span class='tag live'>{len(cards)} brands · {need} need attention</span>"
        "<span class=filters>"
        f"{chip('mine', f'My book ({mine_n})')}{chip('all', f'All accounts ({all_n})')}"
        "<a class=chip href='/agency/team' style='text-decoration:none'>Team</a>"
        "<a class=chip href='#' style='text-decoration:none' "
        "onclick=\"fetch('/api/logout',{method:'POST'}).then(function(){location.href='/';});return false\">Log out</a>"
        "</span></div>"
        "<div class=hsub style='margin-bottom:16px'>Each brand's health at a glance — sorted by $ at "
        "stake. Click a brand to operate inside it (scope switches to that account).</div>"
        f"<div class=fleet>{grid}</div>"
        "<p class=note-s style='margin-top:14px'>Colored left edge = health band "
        "(sage healthy · gold watch · terracotta at-risk). “My book” filters to brands assigned "
        "to the signed-in AM.</p>"
        + (add_form_html or ""))
    body = hubkit.frame(inner, sandbar_left=f"<b>SANDBOX</b> · fleet · {_h.escape(agency_name)}",
                        sandbar_right="env: staging")
    return hubkit.doc("Realify · Fleet", hubkit.AGENCY_CSS,
                      _BUSY_MODAL + _backbar.bar(request) + body)
