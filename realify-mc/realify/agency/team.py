"""R10 agency user management — a service layer over the EXISTING agency_members + grants + invites.
No enforcement rebuilt: effective power on a brand stays = brand envelope ∩ agency-role grant (PDP).

Model: ONE agency org, MANY members (each own login/role), never a shared password. A member's "book"
= the set of grants they hold through the agency's engagements (resolve_actor already derives it).
Roles: Agency Admin / Client Lead (AM) / Ads Specialist / Analyst. Admin/specialist/analyst are granted
across ALL the agency's brands; an AM is assigned a book. Seat cap = 10 members per agency."""
from . import ops, invites, ledger, tenancy
from .actor import resolve_actor


def _scope(cur, actor_uid):
    """Bootstrap RLS for a team op run as the runtime app role: resolve the admin actor (sets the
    actor-selfread GUC) and set brand scope to their grants — the admin holds all-brands grants, so
    this makes every member's grants on the agency's brands readable. Harmless on the harness owner."""
    if actor_uid is None:
        return None
    ctx = resolve_actor(cur, actor_uid)
    if ctx.allowed_tenant_ids:
        tenancy.set_brand_scope(cur, list(ctx.allowed_tenant_ids))
    return ctx

SEAT_CAP = 10
# role key -> (display label, all_brands) — all_brands roles auto-grant across the whole book.
ROLES = {
    "agency_admin":   ("Agency Admin", True),
    "account_manager": ("Client Lead (AM)", False),
    "ads_specialist": ("Ads Specialist", True),
    "analyst":        ("Analyst", True),
}


class SeatCapError(Exception):
    """11th seat blocked."""


class BookNotEmptyError(Exception):
    """Removing a member whose book still has brands (reassign first)."""


class BrandSeatError(Exception):
    """A brand may hold exactly one user seat (a change is a transfer, not a second seat)."""


def _engagements(cur, agency_id):
    cur.execute("SELECT id, tenant_id FROM engagements WHERE agency_id=%s AND status<>'terminated' "
                "ORDER BY tenant_id", (agency_id,))
    return cur.fetchall()


def member_count(cur, agency_id):
    cur.execute("SELECT count(*) FROM agency_members WHERE agency_id=%s", (agency_id,))
    return cur.fetchone()[0]


def _pending_invites(cur, agency_id):
    cur.execute("SELECT count(*) FROM agency_invites WHERE agency_id=%s AND used=false "
                "AND expires_at > now()", (agency_id,))
    return cur.fetchone()[0]


def seats_taken(cur, agency_id):
    """Members + outstanding invites — both consume a seat so a burst of invites can't overrun the cap."""
    return member_count(cur, agency_id) + _pending_invites(cur, agency_id)


def _book(cur, agency_id, uid):
    cur.execute("SELECT DISTINCT e.tenant_id FROM grants g JOIN engagements e ON e.id=g.engagement_id "
                "WHERE e.agency_id=%s AND g.user_id=%s AND e.status<>'terminated' ORDER BY e.tenant_id",
                (agency_id, uid))
    return [r[0] for r in cur.fetchall()]


def list_members(cur, agency_id, actor=None):
    _scope(cur, actor)
    cur.execute("SELECT m.user_id, u.email, u.name, m.role FROM agency_members m JOIN users u ON u.id=m.user_id "
                "WHERE m.agency_id=%s ORDER BY m.created_at", (agency_id,))
    rows = cur.fetchall()
    out = []
    for uid, email, name, role in rows:
        book = _book(cur, agency_id, uid)
        names = []
        for t in book:
            cur.execute("SELECT name FROM tenants WHERE id=%s", (t,))
            r = cur.fetchone()
            names.append(r[0] if r else str(t))
        out.append({"user_id": uid, "email": email, "name": (name or email.split("@")[0]),
                    "role": role, "role_label": ROLES.get(role, (role, False))[0],
                    "book": book, "book_names": names})
    return out


def add_member(cur, agency_id, uid, role, actor=None):
    """Add/update a member with `role`; all-brands roles get a grant on every agency engagement."""
    if role not in ROLES:
        role = "analyst"
    cur.execute("INSERT INTO agency_members(agency_id,user_id,role) VALUES(%s,%s,%s) "
                "ON CONFLICT (agency_id,user_id) DO UPDATE SET role=EXCLUDED.role", (agency_id, uid, role))
    if ROLES[role][1]:                                   # all-brands role -> grant across the whole book
        for eng, tid in _engagements(cur, agency_id):
            tenancy.set_brand_scope(cur, [tid])
            ops.grant_role(cur, actor, eng, tid, uid, role)
    return {"user_id": uid, "role": role}


def invite(cur, agency_id, email, role="analyst"):
    """Seat-capped teammate invite. Raises SeatCapError at the 11th seat. Returns (raw_token, invite_id)."""
    if role not in ROLES:
        raise ValueError("unknown role")
    if seats_taken(cur, agency_id) >= SEAT_CAP:
        raise SeatCapError(f"Seat cap reached ({SEAT_CAP}). Remove or reassign a member before inviting more.")
    return invites.create_agency_invite(cur, agency_id, email, role=role)


def assign_book(cur, agency_id, uid, tenant_ids, actor=None):
    _scope(cur, actor)
    """SET a Client Lead's book to exactly `tenant_ids` (add missing grants; drop grants for brands no
    longer in the book). Ledgered per change. Returns the resulting book."""
    want = set(int(t) for t in tenant_ids)
    engmap = {tid: eng for eng, tid in _engagements(cur, agency_id)}
    have = set(_book(cur, agency_id, uid))
    for tid in want - have:
        if tid in engmap:
            tenancy.set_brand_scope(cur, [tid])
            ops.grant_role(cur, None, engmap[tid], tid, uid, "account_manager")
    for tid in have - want:
        if tid in engmap:
            tenancy.set_brand_scope(cur, [tid])
            cur.execute("DELETE FROM grants WHERE user_id=%s AND engagement_id=%s", (uid, engmap[tid]))
            ledger.append(cur, tid, uid, "grant.revoke", engagement_id=engmap[tid])
    return sorted(want & set(engmap))


def reassign_book(cur, agency_id, from_uid, to_uid, actor=None):
    _scope(cur, actor)
    """Move from_uid's ENTIRE book to to_uid in ONE operation: each grant transfers atomically (no brand
    left unowned), in-flight approvals/proposals move to to_uid, ledgered with a handover note. Returns
    the moved tenant_ids."""
    engmap = {tid: eng for eng, tid in _engagements(cur, agency_id)}
    moved = _book(cur, agency_id, from_uid)
    for tid in moved:
        eng = engmap.get(tid)
        if not eng:
            continue
        tenancy.set_brand_scope(cur, [tid])
        cur.execute("DELETE FROM grants WHERE user_id=%s AND engagement_id=%s", (from_uid, eng))
        ops.grant_role(cur, actor, eng, tid, to_uid, "account_manager")   # target gains atomically
        # in-flight approvals/proposals move to the new owner (never orphaned)
        cur.execute("UPDATE approvals SET maker_user=%s WHERE tenant_id=%s AND maker_user=%s "
                    "AND status IN ('proposed','cosign_pending')", (to_uid, tid, from_uid))
        ledger.append(cur, tid, actor, "book.reassign",
                      payload={"from": from_uid, "to": to_uid, "handover": "agency-approved handover note"})
    return moved


def remove_member(cur, agency_id, uid, reassign_to=None, actor=None):
    _scope(cur, actor)
    """Remove a member. BLOCKED if their book is non-empty and no reassign_to given. With reassign_to,
    the book (and in-flight work) transfers first, then the member + any residual grants are removed."""
    book = _book(cur, agency_id, uid)
    if book and not reassign_to:
        raise BookNotEmptyError(f"{len(book)} brand(s) still assigned — reassign the book first.")
    if reassign_to:
        reassign_book(cur, agency_id, uid, reassign_to, actor=actor)
    for eng, tid in _engagements(cur, agency_id):        # drop any residual grants (all-brands roles)
        cur.execute("DELETE FROM grants WHERE user_id=%s AND engagement_id=%s", (uid, eng))
    cur.execute("DELETE FROM agency_members WHERE agency_id=%s AND user_id=%s", (agency_id, uid))
    return {"removed": uid, "reassigned_to": reassign_to}


# ---- brand = one user seat (Part 8): a brand holds exactly one user; a change is a TRANSFER ----
def _ensure_user(cur, email, tenant_id=None, name=None):
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    r = cur.fetchone()
    if r:
        if name is not None:
            cur.execute("UPDATE users SET name=%s WHERE id=%s", (name, r[0]))
        return r[0]
    cur.execute("INSERT INTO users(email,tenant_id,name,created_at) VALUES(%s,%s,%s,now()::text) RETURNING id",
                (email, tenant_id, name))
    return cur.fetchone()[0]


def seed_team(cur, world_key, agency_id, tenant_ids, personas, country="US"):
    """R10/R9.1: seed a multi-member team deterministically (1 admin + 2 AMs + 1 specialist + 1 analyst)
    with REAL person names + the AMs' books assigned. The client-lead persona user IS the Agency Admin
    seat (all-brands)."""
    from .locale import person_name
    cur.execute("UPDATE users SET name=%s WHERE id=%s", (person_name(country, 0), personas["client_lead_uid"]))
    add_member(cur, agency_id, personas["client_lead_uid"], "agency_admin")
    half = max(1, len(tenant_ids) // 2)
    am1 = _ensure_user(cur, f"sandbox-{world_key}-am1@realify.ai", name=person_name(country, 1))
    am2 = _ensure_user(cur, f"sandbox-{world_key}-am2@realify.ai", name=person_name(country, 2))
    add_member(cur, agency_id, am1, "account_manager")
    add_member(cur, agency_id, am2, "account_manager")
    assign_book(cur, agency_id, am1, tenant_ids[:half])
    assign_book(cur, agency_id, am2, tenant_ids[half:])
    add_member(cur, agency_id, _ensure_user(cur, f"sandbox-{world_key}-ads@realify.ai",
                                            name=person_name(country, 3)), "ads_specialist")
    add_member(cur, agency_id, _ensure_user(cur, f"sandbox-{world_key}-analyst@realify.ai",
                                            name=person_name(country, 4)), "analyst")


def brand_seat(cur, tenant_id):
    cur.execute("SELECT id, email FROM users WHERE tenant_id=%s ORDER BY id LIMIT 1", (tenant_id,))
    r = cur.fetchone()
    return {"user_id": r[0], "email": r[1]} if r else None


def add_brand_seat(cur, tenant_id, email):
    """Add the brand's single owner seat. Rejects a SECOND distinct email (BrandSeatError) — use
    transfer_brand_seat to change the owner."""
    cur.execute("SELECT id, email FROM users WHERE tenant_id=%s ORDER BY id", (tenant_id,))
    rows = cur.fetchall()
    for _uid, e in rows:
        if (e or "").lower() == email.lower():
            return _uid                                   # idempotent: same email
    if rows:
        raise BrandSeatError("A brand can hold only one user seat — changing it is a transfer, not a "
                             "second seat.")
    cur.execute("INSERT INTO users(email,tenant_id,created_at) VALUES(%s,%s,now()::text) RETURNING id",
                (email.lower(), tenant_id))
    return cur.fetchone()[0]


def transfer_brand_seat(cur, tenant_id, new_email, actor=None):
    """Transfer the brand's single seat to a new email: the old email loses access, the new gains it,
    ledgered. Not a second seat."""
    cur.execute("SELECT id, email FROM users WHERE tenant_id=%s ORDER BY id LIMIT 1", (tenant_id,))
    r = cur.fetchone()
    if not r:
        return add_brand_seat(cur, tenant_id, new_email)
    uid, old = r
    cur.execute("UPDATE users SET email=%s WHERE id=%s", (new_email.lower(), uid))
    tenancy.set_brand_scope(cur, [tenant_id])
    ledger.append(cur, tenant_id, actor, "brand.seat.transfer", payload={"from": old, "to": new_email})
    return uid
