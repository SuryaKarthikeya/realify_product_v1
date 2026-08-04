"""R17.2 — the approved-agency onboarding path end to end: the invite link opens a BRANDED in-site
setup page, setting a password SIGNS THE OPERATOR IN and lands them in the agency console (not a raw-JSON
'redirect ok' page), a fresh brand-less agency admin actually resolves (no 'No agency in scope'), and the
SAME /signin routes an agency member to the console. Asserted on endpoints + rendered HTML + outbox.
"""
import re
from realify.mail import dev


def test_invite_to_console_and_unified_login(agency_client, owner_conn):
    client, H = agency_client
    dev.clear()
    # application → approve (provisions the agency + emails the invite link)
    ref = client.post("/api/agencies/intake", data={"agency_name": "Onboarders Co", "contact_name": "Ana",
                      "contact_email": "ana@onboarders.co", "hq_country": "US", "am_headcount": "3",
                      "reporting_hours": "6"}).json()["ref"]
    assert client.post(f"/api/ops/agencies/{ref}/approve", headers=H).json()["ok"]
    body = "\n".join(m["body"] for m in dev.inbox(to="ana@onboarders.co"))
    tok = re.search(r"/agency/invite/([A-Za-z0-9_-]+)", body)
    assert tok, f"no invite link in the workspace-ready email:\n{body}"
    token = tok.group(1)

    # (1) the invite page is BRANDED (in-site shell), not the old bare page
    page = client.get(f"/agency/invite/{token}").text
    assert "authcard" in page and "Set up your agency workspace" in page
    assert f"/api/agency/invite/{token}/accept" in page          # AJAX submit target, not a plain form
    assert "Realify" in page

    # (2) accept → signed in + JSON redirect to the console (the AJAX form navigates there)
    acc = client.post(f"/api/agency/invite/{token}/accept", json={"password": "agencypw1"})
    assert acc.status_code == 200 and acc.json()["ok"] and acc.json()["redirect"] == "/agency/console"

    # (3) the console RENDERS for the fresh, brand-less agency admin — NOT 'No agency in scope'
    console = client.get("/agency/console").text
    assert "No agency in scope" not in console
    assert "Onboarders Co" in console
    assert ("add your first client" in console.lower()) or ("Fleet" in console)   # empty fleet, ready to onboard

    # (4) unified login: sign out, then the SAME /signin login routes this agency member to the console
    client.post("/api/logout")
    login = client.post("/api/login", json={"email": "ana@onboarders.co", "password": "agencypw1"})
    assert login.status_code == 200 and login.json().get("redirect") == "/agency/console"


def test_invalid_invite_is_branded(agency_client, owner_conn):
    client, _H = agency_client
    page = client.get("/agency/invite/definitely-not-a-real-token").text
    assert "Invite link invalid" in page and "authcard" in page   # branded, not a bare page
