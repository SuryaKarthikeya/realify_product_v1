"""Agents persistence — agents, tasks, and the hash-chained Autonomy Ledger. Tenant-scoped (WHERE
tenant_id=?, no RLS). The ledger is append-only + hash-chained: each decision links to the prior row's
hash, so tampering is detectable (same spirit as the agency ledger)."""
import datetime
import hashlib
import json
import uuid

from .base import BaseRepository


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _uid():
    return uuid.uuid4().hex


class AgentRepository(BaseRepository):
    # ---- agents ----
    def create(self, tenant_id, specialist, name, autonomy="observe", guardrails=None, scope=None):
        aid = _uid(); now = _now()
        self.con.execute(
            "INSERT INTO agent(id,tenant_id,specialist,name,status,autonomy,autonomy_by_lens,guardrails,"
            "scope,created_at,updated_at) VALUES(?,?,?,?,'active',?,?,?,?,?,?)",
            (aid, tenant_id, specialist, name, autonomy, json.dumps({}),
             json.dumps(guardrails or []), json.dumps(scope or {}), now, now))
        return aid

    def list(self, tenant_id):
        rows = self.con.execute(
            "SELECT * FROM agent WHERE tenant_id=? ORDER BY created_at", (tenant_id,)).fetchall()
        return [self._agent(dict(r)) for r in rows]

    def get(self, tenant_id, agent_id):
        r = self.con.execute("SELECT * FROM agent WHERE id=? AND tenant_id=?", (agent_id, tenant_id)).fetchone()
        return self._agent(dict(r)) if r else None

    def set_status(self, tenant_id, agent_id, status):
        self.con.execute("UPDATE agent SET status=?,updated_at=? WHERE id=? AND tenant_id=?",
                         (status, _now(), agent_id, tenant_id))

    def set_autonomy(self, tenant_id, agent_id, autonomy):
        self.con.execute("UPDATE agent SET autonomy=?,updated_at=? WHERE id=? AND tenant_id=?",
                         (autonomy, _now(), agent_id, tenant_id))

    @staticmethod
    def _agent(d):
        for k in ("autonomy_by_lens", "guardrails", "scope"):
            try: d[k] = json.loads(d.get(k) or ("{}" if k != "guardrails" else "[]"))
            except Exception: d[k] = {} if k != "guardrails" else []
        return d

    # ---- tasks ----
    def add_task(self, tenant_id, agent_id, name, clock="", cadence="daily", autonomy="observe", scope=None):
        tid = _uid()
        self.con.execute(
            "INSERT INTO agent_task(id,agent_id,tenant_id,name,clock,cadence,autonomy,scope,status,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,'active',?)",
            (tid, agent_id, tenant_id, name, clock, cadence, autonomy, json.dumps(scope or {}), _now()))
        return tid

    def tasks(self, tenant_id, agent_id):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM agent_task WHERE agent_id=? AND tenant_id=? ORDER BY created_at",
            (agent_id, tenant_id)).fetchall()]

    # ---- Autonomy Ledger (hash-chained) ----
    def _last(self, tenant_id):
        r = self.con.execute(
            "SELECT seq, hash FROM agent_decision WHERE tenant_id=? ORDER BY seq DESC LIMIT 1",
            (tenant_id,)).fetchone()
        return (r["seq"], r["hash"]) if r else (0, "")

    def log_decision(self, tenant_id, agent_id, task_id, signal, lens, target_sku, action, detail,
                     value_text, confidence, state, created_at=None):
        seq_prev, prev_hash = self._last(tenant_id)
        seq = seq_prev + 1
        created_at = created_at or _now()
        payload = json.dumps([tenant_id, seq, agent_id, signal, target_sku, action, value_text,
                              confidence, state, created_at, prev_hash], sort_keys=True)
        h = hashlib.sha256(payload.encode()).hexdigest()
        self.con.execute(
            "INSERT INTO agent_decision(id,tenant_id,agent_id,task_id,seq,signal,lens,target_sku,action,"
            "detail,value_text,confidence,state,reversible,prev_hash,hash,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?)",
            (_uid(), tenant_id, agent_id, task_id, seq, signal, lens, target_sku, action,
             json.dumps(detail or {}), value_text, confidence, state, prev_hash, h, created_at))
        return h

    def ledger(self, tenant_id, limit=100, state=None):
        q = "SELECT * FROM agent_decision WHERE tenant_id=?"
        args = [tenant_id]
        if state and state != "all":
            q += " AND state=?"; args.append(state)
        q += " ORDER BY seq DESC LIMIT ?"; args.append(limit)
        out = []
        for r in self.con.execute(q, args).fetchall():
            d = dict(r)
            try: d["detail"] = json.loads(d.get("detail") or "{}")
            except Exception: d["detail"] = {}
            out.append(d)
        return out

    def ledger_intact(self, tenant_id):
        """Re-walk the chain; True if every hash links to its predecessor (tamper check)."""
        rows = self.con.execute(
            "SELECT * FROM agent_decision WHERE tenant_id=? ORDER BY seq ASC", (tenant_id,)).fetchall()
        prev = ""
        for r in rows:
            payload = json.dumps([r["tenant_id"], r["seq"], r["agent_id"], r["signal"], r["target_sku"],
                                  r["action"], r["value_text"], r["confidence"], r["state"],
                                  r["created_at"], prev], sort_keys=True)
            if hashlib.sha256(payload.encode()).hexdigest() != r["hash"]:
                return False
            prev = r["hash"]
        return True
