"""R11.2 (Postgres/agency): the guided-run teleprompter RIDES the brand drill-in (and stacks above the
scope bar) so Next/Exit stay reachable inside a brand — end-to-end through the app."""
import re

from realify.agency import sandbox


def test_guided_bar_rides_drilldown_and_persona_flip(agency_client, owner_conn):
    client, H = agency_client
    sandbox.load_preset(owner_conn.cursor(), "us_pilot"); owner_conn.commit()
    # start the customer walkthrough
    assert client.post("/api/ops/sandbox/guided-run/start", headers=H, json={"name": "customer"}).status_code == 200
    # Next → lands on the brand drill-in
    nav = client.post("/api/ops/sandbox/guided-run/next", headers=H).json()["redirect"]
    assert re.match(r"^/agency/brand/\d+$", nav)
    # R15 Part 0 — the drill-in (nav) now 303→ the REAL five-lens app; the guided teleprompter rides it,
    # STACKED above the back-to-hub bar (R11.2 stacking preserved on the unified surface).
    body = client.get(nav).text                                     # follows the redirect to the real app
    assert "r9guided" in body and "Next →" in body                  # teleprompter present on the surface
    assert "r9backbar" in body                                      # ...above the back-to-hub bar
    assert body.index("r9guided") < body.index("r9backbar")         # guided on top
    assert "has-guided" in body                                     # stacked-bar offset armed
    # advance to the persona-flip (portal) step — the bar still rides the new surface
    r = nav
    for _ in range(5):
        d = client.post("/api/ops/sandbox/guided-run/next", headers=H).json()
        if d.get("done"):
            break
        r = d["redirect"]
        if r.startswith("/brand/portal/"):
            assert "r9guided" in client.get(r).text                 # persists after the persona flip
            break
    # Exit clears the bar on whatever surface we're on
    assert client.post("/api/ops/sandbox/guided-run/exit", headers=H).json()["ok"] is True
    assert "r9guided" not in client.get(nav).text
