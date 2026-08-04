"""R10 agency user management — /agency/team (mockup h9) + the team APIs. Built on tokens.py so it
matches the marketing/hub system. Reuses the R0 invite/accept + the grant machinery via
realify.agency.team; enforcement (envelope⊗grant) is unchanged."""
import html

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from ..agency import team, tenancy, db as agency_db
from ..agency.actor import resolve_actor
from ..agency.guard import require_agency_console
from .deps import current
from realify.site.tokens import SHELL_CSS as _SHELL, state_page as _state_page
from realify.site import backbar as _backbar

router = APIRouter()

# h9 classes lifted from the hub mockup (on top of the shared tokens).
_CSS = _SHELL + """
body{background:#E9E3D8}#wrap{max-width:1120px;margin:0 auto;padding:24px 30px 70px}
.frame{background:var(--bg);border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 2px 6px rgba(26,26,26,.07),0 16px 44px rgba(26,26,26,.09)}
.pad{padding:26px 30px}.htitle{font-family:var(--serif);font-size:23px;font-weight:700;margin:0}
.chip{display:inline-block;font-size:12.5px;font-weight:600;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:100px;padding:5px 13px;cursor:pointer}
.chip:hover{border-color:var(--ink)}
.hsub{color:var(--muted);font-size:13.5px;margin:4px 0 0}
.step{background:var(--card);border:1px solid var(--line);border-radius:14px;margin-top:16px;overflow:hidden}
.step-h{display:flex;align-items:center;gap:12px;padding:16px 20px;border-bottom:1px solid #EDE7DA;background:#FBF9F4}
.step-n{width:26px;height:26px;border-radius:50%;background:var(--ink);color:#fff;font-family:var(--mono);font-size:13px;font-weight:600;text-align:center;line-height:26px}
.step-h h3{margin:0;font-size:15px}.step-body{padding:8px 20px}
.seedrow{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 0;border-bottom:1px solid #EDE7DA;font-size:13.5px}
.seedrow:last-child{border-bottom:none}.seedrow .meta{color:var(--muted);font-size:12px;margin-top:3px}
.roletag{display:inline-block;font-family:var(--mono);font-size:10px;letter-spacing:.06em;border-radius:100px;padding:2px 9px;background:#EAF0F5;color:var(--slate);margin-left:8px}
.settingbar{display:flex;gap:14px;background:#FBF9F4;border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin-top:16px;font-size:13px}
.cols2{display:grid;grid-template-columns:1fr 1fr;gap:0 18px;margin-top:16px}
.msg{font-size:13px;margin-top:12px;min-height:18px}.err{color:var(--red)}.ok{color:var(--green)}
select,input{border:1.5px solid var(--line);border-radius:8px;padding:8px 10px;font-size:13px;background:#fff}
.mono{font-family:var(--mono)}
"""


def _agency_admin(request):
    """Return (uid, agency_id) if the session actor is an Agency Admin of a (single) agency, else None."""
    uid, _ = current(request)
    if not uid:
        return None
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        ctx = resolve_actor(cur, uid)                    # sets the actor GUC for the resolve
        from ..agency import fleet_data
        _tid = current(request)[1]
        ag, _ = fleet_data.resolve_agency(cur, uid, _tid, list(ctx.agency_ids))  # grant-independent (agency_members)
        role = None
        if ag:
            cur.execute("SELECT role FROM agency_members WHERE agency_id=%s AND user_id=%s", (ag, uid))
            r = cur.fetchone()
            role = r[0] if r else None
        conn.rollback()
        return (uid, ag) if (ag and role == "agency_admin") else None
    finally:
        conn.close()


async def _body(request):
    try:
        return dict(await request.form()) or await request.json()
    except Exception:
        try:
            return await request.json()
        except Exception:
            return {}


@router.get("/agency/team", response_class=HTMLResponse, dependencies=[Depends(require_agency_console)])
def team_page(request: Request):
    who = _agency_admin(request)
    if not who:
        return HTMLResponse(_state_page("Agency admin required", "Sign in as an agency admin to manage the team & books.", "Staff only"), status_code=403)
    uid, ag = who
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        members = team.list_members(cur, ag, actor=uid)
        is_owner = _is_owner(cur, ag, uid)           # only the founding owner manages the roster (R19)
        brands = team._engagements(cur, ag)          # (eng, tid)
        names = {}
        for _e, tid in brands:
            cur.execute("SELECT name FROM tenants WHERE id=%s", (tid,))
            names[tid] = (cur.fetchone() or [str(tid)])[0]
        taken = team.seats_taken(cur, ag)
        conn.rollback()
    finally:
        conn.close()

    def brand_opts(sel=None):
        return "".join(f"<option value={tid}>{html.escape(names[tid])}</option>" for _e, tid in brands)
    member_opts = "".join(f"<option value={m['user_id']}>{html.escape(m['name'])} · {html.escape(m['role_label'])}</option>"
                          for m in members)

    def mrow(m):
        book = (", ".join(html.escape(n) for n in m["book_names"]) if m["book"]
                else ("all brands" if m["role"] != "account_manager" else "no brands yet"))
        act = ""
        if is_owner:                                 # roster management is owner-only
            act = ("<button class='btn sm' data-viewas=%d>View as</button>" % m["user_id"])
            if m["role"] == "account_manager":
                act = ("<button class='btn sm' data-assign=%d>Assign book</button> " % m["user_id"]) + act
            if m["user_id"] != uid:                  # the owner can't delete themselves
                act += " <button class='btn sm' data-remove=%d>Remove</button>" % m["user_id"]
        return (f"<div class=seedrow><span><b>{html.escape(m['name'])}</b>"
                f"<span class=roletag>{html.escape(m['role_label'])}</span>"
                f"<div class=meta>book: {book}</div></span><span>{act}</span></div>")
    rows = "".join(mrow(m) for m in members) or "<div class=seedrow><i>No members yet.</i></div>"
    role_opts = "".join(f"<option value={k}>{html.escape(v[0])}</option>" for k, v in team.ROLES.items())
    return HTMLResponse(
        "<!doctype html><html lang=en><head><meta charset=utf-8><meta name=robots content='noindex'>"
        "<meta name=viewport content='width=device-width,initial-scale=1'><title>Team &amp; books</title>"
        f"<style>{_CSS}</style></head><body>" + _backbar.bar(request) + "<div id=wrap><div class=frame><div class=pad>"
        "<div style='display:flex;align-items:center;gap:12px'>"
        "<a href='/agency/console' class=chip style='text-decoration:none'>← Fleet</a>"
        "<h2 class=htitle>Team &amp; books</h2>"
        f"<span class=roletag>{len(members)}/{team.SEAT_CAP} seats</span>"
        "<a href='#' class=chip style='text-decoration:none;margin-left:auto' "
        "onclick=\"fetch('/api/logout',{method:'POST'}).then(function(){location.href='/';});return false\">Log out</a>"
        "</div>"
        "<p class=hsub>One agency, many seats. Each person signs in as themselves; what they can do on a "
        "brand = the brand's envelope ∩ their agency role.</p>"
        "<div class=step><div class=step-h><span class=step-n>◷</span><h3>Members &amp; their books</h3></div>"
        f"<div class=step-body>{rows}</div></div>"
        "<div class=cols2>"
        "<div class=step><div class=step-h><span class=step-n>+</span><h3>Invite teammate</h3></div>"
        "<div class=step-body style='padding:16px 20px'>"
        "<input id=invEmail type=email placeholder='teammate@email.com' style='width:100%;margin-bottom:8px'>"
        f"<select id=invRole style='width:100%'>{role_opts}</select>"
        "<div style='margin-top:10px'><button class='btn btn-blue sm' id=btnInvite>+ Invite teammate</button></div>"
        "<div class=msg id=invMsg></div></div></div>"
        "<div class=step><div class=step-h><span class=step-n>⇄</span><h3>Reassign a book</h3></div>"
        "<div class=step-body style='padding:16px 20px'>"
        f"<label class=mono style='font-size:11px'>from</label><select id=reFrom style='width:100%;margin-bottom:8px'>{member_opts}</select>"
        f"<label class=mono style='font-size:11px'>to</label><select id=reTo style='width:100%'>{member_opts}</select>"
        "<div style='margin-top:10px'><button class='btn sm' id=btnReassign>Transfer book →</button></div>"
        "<div class=msg id=reMsg></div></div></div></div>"
        "<div class=settingbar><div><b>How work is shared, not passwords.</b> Two AMs never log in as the "
        "same user — each holds their own grant; RLS + envelope⊗grant means an AM sees their book, a "
        "specialist sees their lens, and neither exceeds what a brand granted the agency.</div></div>"
        "</div></div></div>"
        "<script>"
        # R19: only the agency OWNER manages the roster — hide the invite/reassign block for everyone else
        # (per-member action buttons are already owner-gated server-side + in mrow; endpoints 403 non-owners).
        f"var IS_OWNER={'true' if is_owner else 'false'};"
        "if(!IS_OWNER){var _c=document.querySelector('.cols2');if(_c)_c.style.display='none';}"
        f"var BRANDS=[{','.join(str(tid) for _e,tid in brands)}];var BNAMES={{{','.join('%d:%s'%(tid,_js(names[tid])) for _e,tid in brands)}}};"
        "function post(u,b){return fetch(u,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(b||{})});}"
        "document.getElementById('btnInvite').addEventListener('click',async function(){var m=document.getElementById('invMsg');"
        "var r=await post('/api/agency/team/invite',{email:document.getElementById('invEmail').value,role:document.getElementById('invRole').value});"
        "var d=await r.json().catch(function(){return{};});m.className='msg '+(r.ok?'ok':'err');m.textContent=r.ok?('Invite sent to '+d.email+' ('+d.role+').'):((d&&d.error)||'Failed.');});"
        "document.getElementById('btnReassign').addEventListener('click',async function(){var m=document.getElementById('reMsg');"
        "var f=+document.getElementById('reFrom').value,t=+document.getElementById('reTo').value;if(f===t){m.className='msg err';m.textContent='Pick two different members.';return;}"
        "var r=await post('/api/agency/team/reassign',{from_uid:f,to_uid:t});var d=await r.json().catch(function(){return{};});"
        "m.className='msg '+(r.ok?'ok':'err');m.textContent=r.ok?('Moved '+d.moved+' brand(s). Handover note queued.'):((d&&d.error)||'Failed.');if(r.ok)setTimeout(function(){location.reload();},900);});"
        "document.querySelectorAll('[data-viewas]').forEach(function(b){b.addEventListener('click',async function(){"
        "var r=await post('/api/agency/team/view-as',{uid:+b.dataset.viewas});var d=await r.json().catch(function(){return{};});if(r.ok&&d.redirect)location.href=d.redirect;else alert((d&&d.error)||'Failed.');});});"
        "document.querySelectorAll('[data-assign]').forEach(function(b){b.addEventListener('click',async function(){"
        "var picks=prompt('Assign brands (comma tenant ids) from: '+BRANDS.join(','));if(picks===null)return;"
        "var ids=picks.split(',').map(function(x){return +x.trim();}).filter(Boolean);"
        "var r=await post('/api/agency/team/assign',{uid:+b.dataset.assign,tenant_ids:ids});var d=await r.json().catch(function(){return{};});"
        "alert(r.ok?('Book set: '+(d.book||[]).length+' brand(s).'):((d&&d.error)||'Failed.'));if(r.ok)location.reload();});});"
        "document.querySelectorAll('[data-remove]').forEach(function(b){b.addEventListener('click',async function(){"
        "var r=await post('/api/agency/team/remove',{uid:+b.dataset.remove});var d=await r.json().catch(function(){return{};});"
        "if(r.ok){location.reload();return;}var to=prompt((d&&d.error||'')+'\\nReassign this book to member uid:');if(!to)return;"
        "var r2=await post('/api/agency/team/remove',{uid:+b.dataset.remove,reassign_to:+to});alert(r2.ok?'Removed + reassigned.':'Failed.');if(r2.ok)location.reload();});});"
        "</script></body></html>")


def _js(s):
    return '"' + html.escape(str(s)).replace('"', '\\"') + '"'


def _is_owner(cur, agency_id, uid):
    """May this user manage the roster? The founding owner (agencies.owner_user_id) only — EXCEPT an
    UNOWNED agency (owner_user_id IS NULL: sandbox/preset/legacy worlds with no accept flow) stays
    manageable by any agency_admin, preserving prior behavior (R19)."""
    cur.execute("SELECT owner_user_id FROM agencies WHERE id=%s", (agency_id,))
    r = cur.fetchone()
    if not r:
        return False
    return r[0] is None or r[0] == uid


def _do(request, fn, owner_only=False):
    who = _agency_admin(request)
    if not who:
        return None, JSONResponse({"ok": False, "error": "agency admin required"}, status_code=403)
    uid, ag = who
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        if owner_only and not _is_owner(cur, ag, uid):
            conn.rollback()
            return None, JSONResponse({"ok": False, "error": "only the agency owner can manage teammates"},
                                      status_code=403)
        res = fn(cur, uid, ag)
        conn.commit()
        return res, None
    except (team.SeatCapError, team.BookNotEmptyError, team.BrandSeatError) as e:
        conn.rollback()
        code = 409 if isinstance(e, team.BookNotEmptyError) else 403 if isinstance(e, team.SeatCapError) else 409
        return None, JSONResponse({"ok": False, "error": str(e)}, status_code=code)
    except ValueError as e:
        conn.rollback()
        return None, JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    finally:
        conn.close()


@router.post("/api/agency/team/invite", dependencies=[Depends(require_agency_console)])
async def team_invite(request: Request):
    b = await _body(request)
    email = (b.get("email") or "").strip()
    role = b.get("role") or "agency_admin"               # R19 default: full-operate, all-brands teammate
    if "@" not in email:
        return JSONResponse({"ok": False, "error": "valid email required"}, status_code=400)

    def _fn(cur, uid, ag):
        token, iid = team.invite(cur, ag, email, role)
        if token:                                        # email the single-use invite via the mail abstraction
            _send_invite(cur, ag, email, token)
        return {"invite_id": iid, "email": email, "role": role}
    res, err = _do(request, _fn, owner_only=True)         # only the agency owner invites teammates
    return err or JSONResponse({"ok": True, **res})


def _send_invite(cur, agency_id, email, token):
    from .. import mail, config
    from ..agency import mailcfg
    base = (config.APP_URL or "https://realifyai.app").rstrip("/")
    try:
        mail.send(email, "You're invited to a Realify agency workspace",
                  f"You've been invited to join a Realify for Agencies workspace. Set your password and "
                  f"sign in (single-use, expires in 7 days):\n{base}/agency/invite/{token}",
                  from_addr=mailcfg.from_addr(), reply_to=mailcfg.reply_to())
    except Exception as e:                               # pragma: no cover
        print(f"[team-invite] mail failed for {email}: {e}", flush=True)


@router.post("/api/agency/team/assign", dependencies=[Depends(require_agency_console)])
async def team_assign(request: Request):
    b = await _body(request)
    res, err = _do(request, lambda cur, uid, ag: {"book": team.assign_book(cur, ag, int(b["uid"]),
                                                                           b.get("tenant_ids") or [], actor=uid)})
    return err or JSONResponse({"ok": True, **res})


@router.post("/api/agency/team/reassign", dependencies=[Depends(require_agency_console)])
async def team_reassign(request: Request):
    b = await _body(request)
    res, err = _do(request, lambda cur, uid, ag: {"moved": len(team.reassign_book(
        cur, ag, int(b["from_uid"]), int(b["to_uid"]), actor=uid))})
    return err or JSONResponse({"ok": True, **res})


@router.post("/api/agency/team/remove", dependencies=[Depends(require_agency_console)])
async def team_remove(request: Request):
    """Owner-only. Removes a teammate from the agency AND hard-deletes their Realify account (R19
    decision). The account-delete runs AFTER the membership txn commits, via the ONE lifecycle
    (execute_user), which clears their hash-chained ledger footprint first so the users-row delete never
    trips ledger_actor_user_fkey."""
    b = await _body(request)
    target = int(b.get("uid") or 0)

    def _fn(cur, uid, ag):
        if target == uid:
            raise ValueError("You can't remove yourself (the agency owner).")
        cur.execute("SELECT 1 FROM agency_members WHERE agency_id=%s AND user_id=%s", (ag, target))
        if not cur.fetchone():
            raise ValueError("Not a member of this agency.")
        # drop membership + any residual grants now; clear the user's ledger footprint so the hard-delete
        # (below, post-commit) doesn't hit the RESTRICT ledger_actor_user_fkey.
        cur.execute("DELETE FROM agency_members WHERE agency_id=%s AND user_id=%s", (ag, target))
        cur.execute("SELECT id FROM tenants")
        tenancy.set_brand_scope(cur, [r[0] for r in cur.fetchall()])
        cur.execute("DELETE FROM ledger WHERE actor_user=%s", (target,))
        return {"removed": target}
    res, err = _do(request, _fn, owner_only=True)
    if err:
        return err
    from .. import lifecycle, db as _db
    con = _db.connect()                                   # hard-delete the user account (+ their empty org)
    try:
        lifecycle.execute_user(con, target)
    finally:
        con.close()
    return JSONResponse({"ok": True, **res})


@router.post("/api/agency/team/view-as", dependencies=[Depends(require_agency_console)])
async def team_view_as(request: Request):
    b = await _body(request)
    who = _agency_admin(request)
    if not who:
        return JSONResponse({"ok": False, "error": "agency admin required"}, status_code=403)
    _uid, ag = who
    target = int(b.get("uid") or 0)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        team._scope(cur, _uid)
        cur.execute("SELECT role FROM agency_members WHERE agency_id=%s AND user_id=%s", (ag, target))
        if not cur.fetchone():
            return JSONResponse({"ok": False, "error": "not a member of this agency"}, status_code=404)
        book = team._book(cur, ag, target)
        conn.rollback()
    finally:
        conn.close()
    request.session["uid"] = target
    request.session["tid"] = (book[0] if book else request.session.get("tid"))
    request.session["acting_as"] = {"role": "Agency teammate", "tenant": f"book of {len(book)} brand(s)",
                                    "via": None}
    return JSONResponse({"ok": True, "redirect": "/agency/console"})
