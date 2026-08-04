"""R10 (Postgres/agency suite): agency user management — team screen, seat cap, invite→accept e2e,
book assignment + My-book filter, atomic reassignment, safe member removal, brand=one-user, and the
multi-member seed. Reuses the existing agency_members + grants + invites machinery."""
import os
import re
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realify.agency import sandbox, team


def _admin_session(agency_client, owner_conn):
    """Load the US pilot and put the client (session) in the agency-admin seat via impersonation."""
    client, H = agency_client
    sandbox.load_preset(owner_conn.cursor(), "us_pilot"); owner_conn.commit()
    r = client.post("/api/ops/sandbox/assume", headers=H, json={"persona": "client_lead"})
    assert r.status_code == 200
    return client, H


# ---- Part 9 seed + Part 1 team screen (mockup h9) + no-dead-controls ----
def test_team_seeded_and_screen_renders(agency_client, owner_conn):
    client, H = _admin_session(agency_client, owner_conn)
    body = client.get("/agency/team").text
    assert "Team &amp; books" in body and "Members &amp; their books" in body      # h9 headings
    assert "Agency Admin" in body and "Client Lead (AM)" in body and "Ads Specialist" in body and "Analyst" in body
    assert "Invite teammate" in body and "Reassign a book" in body
    # no dead controls: every button is wired (id+listener, data-*, or onclick)
    for m in re.finditer(r"<button\b([^>]*)>", body):
        a = m.group(1)
        assert ("id=" in a) or ("data-" in a) or ("onclick=" in a), f"dead team button: {a}"
    # seeded 5 members (1 admin + 2 AMs + specialist + analyst)
    cur = owner_conn.cursor()
    ag = sandbox._scenario_agency(cur, "us_pilot")
    assert team.member_count(cur, ag) == 5


# ---- Part 2 seat cap: 10 ok, 11th blocked with a message ----
def test_seat_cap_10(agency_client, owner_conn):
    client, _H = _admin_session(agency_client, owner_conn)
    cur = owner_conn.cursor()
    ag = sandbox._scenario_agency(cur, "us_pilot")
    # already 5 members; invite up to the cap (10 seats total), then the next is blocked
    ok = 0
    for i in range(20):
        r = client.post("/api/agency/team/invite", json={"email": f"seat{i}@x.com", "role": "analyst"})
        if r.status_code == 200:
            ok += 1
        else:
            assert r.status_code == 403 and "Seat cap" in r.json()["error"]
            break
    assert ok == 5                                          # 5 members + 5 invites = 10 seats; 11th blocked
    assert team.seats_taken(cur, ag) == 10


# ---- Part 4 invite → accept e2e (reuses R0 invite/accept); new member joins with the role ----
def test_invite_accept_e2e(agency_client, owner_conn):
    client, _H = _admin_session(agency_client, owner_conn)
    cur = owner_conn.cursor()
    ag = sandbox._scenario_agency(cur, "us_pilot")
    email = f"newam-{secrets.token_hex(3)}@x.com"
    token, _iid = team.invite(cur, ag, email, "account_manager"); owner_conn.commit()
    assert token
    fresh = agency_client[0].__class__(__import__("run").make_app())   # a clean client (no session)
    r = fresh.post(f"/api/agency/invite/{token}/accept", json={"password": "password1"})
    assert r.status_code == 200 and r.json()["ok"]
    cur.execute("SELECT m.role FROM agency_members m JOIN users u ON u.id=m.user_id "
                "WHERE m.agency_id=%s AND u.email=%s", (ag, email))
    assert cur.fetchone()[0] == "account_manager"           # joined as the invited role


# ---- Part 5 book assignment + My-book filter ----
def test_book_assignment_and_my_book_filter(agency_client, owner_conn):
    client, H = _admin_session(agency_client, owner_conn)
    cur = owner_conn.cursor()
    ag = sandbox._scenario_agency(cur, "us_pilot")
    brands = [t for _e, t in team._engagements(cur, ag)]
    am = team._ensure_user(cur, f"amx-{secrets.token_hex(3)}@x.com")
    team.add_member(cur, ag, am, "account_manager")
    team.assign_book(cur, ag, am, brands[:2]); owner_conn.commit()
    assert sorted(team._book(cur, ag, am)) == sorted(brands[:2])
    # impersonate that AM → My book shows only their 2 brands
    client.post("/api/agency/team/view-as", json={"uid": am})
    q = client.get("/agency/queue?book=mine").text
    cur.execute("SELECT name FROM tenants WHERE id=ANY(%s)", (brands[:2],))
    mine = [n for (n,) in cur.fetchall()]
    cur.execute("SELECT name FROM tenants WHERE id=ANY(%s)", (brands[2:],))
    not_mine = [n for (n,) in cur.fetchall()]
    for n in mine:
        assert n in q
    assert not any(n in q for n in not_mine)                # AM cannot see brands outside their book


# ---- Part 6 atomic reassignment ----
def test_atomic_reassign(agency_client, owner_conn):
    _client, _H = _admin_session(agency_client, owner_conn)
    cur = owner_conn.cursor()
    ag = sandbox._scenario_agency(cur, "us_pilot")
    brands = [t for _e, t in team._engagements(cur, ag)]
    a = team._ensure_user(cur, f"a-{secrets.token_hex(3)}@x.com")
    b = team._ensure_user(cur, f"b-{secrets.token_hex(3)}@x.com")
    team.add_member(cur, ag, a, "account_manager"); team.add_member(cur, ag, b, "account_manager")
    team.assign_book(cur, ag, a, brands[:3]); owner_conn.commit()
    moved = team.reassign_book(cur, ag, a, b); owner_conn.commit()
    assert sorted(moved) == sorted(brands[:3])
    assert team._book(cur, ag, a) == []                     # source empty
    assert sorted(team._book(cur, ag, b)) == sorted(brands[:3])   # target has them
    # no brand left unowned: every reassigned brand still has an owner grant
    for t in brands[:3]:
        cur.execute("SELECT count(*) FROM grants g JOIN engagements e ON e.id=g.engagement_id "
                    "WHERE e.tenant_id=%s AND g.user_id=%s", (t, b))
        assert cur.fetchone()[0] == 1
    cur.execute("SELECT count(*) FROM ledger WHERE action='book.reassign' AND tenant_id=ANY(%s)", (brands[:3],))
    assert cur.fetchone()[0] >= 3                            # ledgered per brand


# ---- Part 7 member removal edge cases ----
def test_member_removal_safe(agency_client, owner_conn):
    _client, _H = _admin_session(agency_client, owner_conn)
    cur = owner_conn.cursor()
    ag = sandbox._scenario_agency(cur, "us_pilot")
    brands = [t for _e, t in team._engagements(cur, ag)]
    a = team._ensure_user(cur, f"rem-{secrets.token_hex(3)}@x.com")
    lead = team._ensure_user(cur, f"lead-{secrets.token_hex(3)}@x.com")
    team.add_member(cur, ag, a, "account_manager"); team.add_member(cur, ag, lead, "account_manager")
    team.assign_book(cur, ag, a, brands[:2]); owner_conn.commit()
    # removing with a non-empty book is BLOCKED
    try:
        team.remove_member(cur, ag, a); owner_conn.rollback()
        assert False, "should have blocked"
    except team.BookNotEmptyError:
        owner_conn.rollback()
    # reassign-on-remove moves the book to the lead and removes the member
    team.remove_member(cur, ag, a, reassign_to=lead); owner_conn.commit()
    cur.execute("SELECT count(*) FROM agency_members WHERE agency_id=%s AND user_id=%s", (ag, a))
    assert cur.fetchone()[0] == 0
    assert sorted(team._book(cur, ag, lead)) [:2] == sorted(brands[:2])[:2]   # book landed on the lead


# ---- Part 8 brand = one user (second seat rejected; transfer works, ledgered) ----
def test_brand_one_user(owner_conn):
    cur = owner_conn.cursor()
    st = sandbox.load_preset(cur, "us_pilot"); owner_conn.commit()
    brand = st["brands"][3]["tenant_id"]   # a managed brand with no pre-seeded owner seat
    team.add_brand_seat(cur, brand, "owner1@brand.com"); owner_conn.commit()
    try:
        team.add_brand_seat(cur, brand, "owner2@brand.com")   # second distinct email
        owner_conn.rollback()
        assert False, "second seat should be rejected"
    except team.BrandSeatError:
        owner_conn.rollback()
    # transfer changes the single seat (old loses, new gains), ledgered
    team.transfer_brand_seat(cur, brand, "owner2@brand.com"); owner_conn.commit()
    assert team.brand_seat(cur, brand)["email"] == "owner2@brand.com"
    cur.execute("SELECT count(*) FROM ledger WHERE tenant_id=%s AND action='brand.seat.transfer'", (brand,))
    assert cur.fetchone()[0] >= 1
