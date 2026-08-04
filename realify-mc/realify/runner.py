"""TaskRunner seam (#005 1e) — the single place async/background work is executed and tracked.

Today: an in-process runner that records job state in the `jobs` table. `ThreadTaskRunner` runs in
a daemon thread (returns the job_id immediately; poll via `get`); `InlineTaskRunner` runs
synchronously (deterministic — used by tests and synchronous callers). The interface is
deliberately small —

    submit(kind, fn, tenant_id=None) -> job_id
    get(job_id) -> {id, tenant_id, kind, state, result, error, ...} | None

— so the future heavy implementation (an external queue + workers, e.g. for real-time incremental
runs §3H, agent trigger-and-await §3K, or out-of-process model serving §3F) drops in behind this
seam without changing any caller. Swap `DEFAULT` for a queue-backed runner and call sites are
untouched.

`fn` is a zero-arg callable returning a JSON-serialisable result (or None). Exceptions are caught
and recorded as the job's `error` — a failed job never crashes the runner or its caller.
"""
import json
import threading

from . import db
from .repositories.job_repo import JobRepository


def _record(job_id, state, result=None, error=None):
    con = db.connect()
    try:
        JobRepository(con).set_state(job_id, state, result, error)
    finally:
        con.close()


def _serialize(out):
    if out is None:
        return None
    try:
        return json.dumps(out)
    except (TypeError, ValueError):
        return json.dumps(str(out))


def _run(job_id, fn):
    _record(job_id, "running")
    try:
        _record(job_id, "done", result=_serialize(fn()))
    except Exception as e:  # a job failure must never crash the runner
        _record(job_id, "error", error=str(e)[:500])


def _new_job(tenant_id, kind):
    con = db.connect()
    try:
        return JobRepository(con).create(tenant_id, kind)
    finally:
        con.close()


class TaskRunner:
    def submit(self, kind, fn, tenant_id=None):
        raise NotImplementedError

    def get(self, job_id):
        con = db.connect()
        try:
            return JobRepository(con).get(job_id)
        finally:
            con.close()


class InlineTaskRunner(TaskRunner):
    """Runs the work synchronously before returning the job_id. Deterministic; used by tests."""
    def submit(self, kind, fn, tenant_id=None):
        job_id = _new_job(tenant_id, kind)
        _run(job_id, fn)
        return job_id


class ThreadTaskRunner(TaskRunner):
    """Runs the work in a daemon thread; returns the job_id immediately (poll via get())."""
    def submit(self, kind, fn, tenant_id=None):
        job_id = _new_job(tenant_id, kind)
        threading.Thread(target=_run, args=(job_id, fn), daemon=True).start()
        return job_id


# Default runner. Swap this for an external-queue-backed runner without touching callers.
DEFAULT = ThreadTaskRunner()


def submit(kind, fn, tenant_id=None, runner=None):
    return (runner or DEFAULT).submit(kind, fn, tenant_id)


def get(job_id, runner=None):
    return (runner or DEFAULT).get(job_id)


def run_pipeline_async(tenant_id, runner=None):
    """The real use of the seam: trigger an (incremental) pipeline run as a tracked job. This is
    the entry point real-time inbound events and agent trigger-and-await build on (§3H / §3K).
    Behaviour-preserving: the existing batch scheduler and provisioning flows are unchanged; this
    is an additional, pollable way to run the pipeline on demand."""
    from .pipeline.materialize import run_pipeline
    return submit("pipeline_run", lambda: run_pipeline(tenant_id), tenant_id=tenant_id, runner=runner)
