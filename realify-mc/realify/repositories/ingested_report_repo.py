"""Ingested-report fingerprints (0008): dedup identical re-uploads.

Stores a SHA-256 of each ingested report's parsed+normalized table per tenant. The upload and
onboarding paths call `partition()` to split a batch into fresh vs. 100%-duplicate tables, then
`record_fresh()` after a successful commit. Identity only ever matches genuinely identical data,
so a distinct report is never dropped; semantic overlap stays with the report_overlap flow.
"""
import datetime

from .base import BaseRepository


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class IngestedReportRepository(BaseRepository):
    def seen(self, tenant_id, content_hash):
        row = self.con.execute(
            "SELECT filename, report_type, ingested_at FROM ingested_reports "
            "WHERE tenant_id=? AND content_hash=?", (tenant_id, content_hash)).fetchone()
        return dict(row) if row else None

    def record(self, tenant_id, content_hash, report_type, filename):
        self.con.execute(
            "INSERT OR REPLACE INTO ingested_reports"
            "(tenant_id, content_hash, report_type, filename, ingested_at) VALUES(?,?,?,?,?)",
            (tenant_id, content_hash, report_type, filename, _now()))

    def partition(self, tenant_id, tables):
        """Split loaded (name, df) tables into fresh [(name, df, hash)] and duplicates
        [(name, prior_filename, prior_ingested_at)] via normalized-content fingerprints. A table
        duplicated within the same batch counts as a duplicate of its first occurrence."""
        from realify.ingest.report_ingest import content_hash
        fresh, duplicates, seen_batch = [], [], {}
        for name, df in tables:
            h = content_hash(df)
            prior = self.seen(tenant_id, h)
            if prior:
                duplicates.append((name, prior.get("filename"), prior.get("ingested_at")))
            elif h in seen_batch:
                duplicates.append((name, seen_batch[h], None))
            else:
                seen_batch[h] = name
                fresh.append((name, df, h))
        return fresh, duplicates

    def record_fresh(self, tenant_id, fresh, report_types):
        """Fingerprint each freshly-ingested, *recognized* report so a later re-upload is caught."""
        from realify.ingest.report_ingest import detect_report_type, UNKNOWN
        for name, df, h in fresh:
            rt = (report_types or {}).get(name) or detect_report_type(df.columns)
            if rt != UNKNOWN:
                self.record(tenant_id, h, rt, name)
