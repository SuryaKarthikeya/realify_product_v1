"""Guard the Postgres connection wrapper's `with` support. Regression for the production 500s
('_PGConnection object does not support the context manager protocol') — SQLite's connection
supports `with` natively so the tests never caught this; here we assert the PG wrapper matches,
without needing a live Postgres."""
import pytest
from realify.dbengine import _PGConnection


class _FakeRaw:
    def __init__(self):
        self.committed = self.rolledback = self.closed = False
    def commit(self): self.committed = True
    def rollback(self): self.rolledback = True
    def close(self): self.closed = True


def test_with_block_commits_and_closes_on_success():
    raw = _FakeRaw()
    with _PGConnection(raw) as con:
        assert con is not None
    assert raw.committed and raw.closed and not raw.rolledback


def test_with_block_rolls_back_and_closes_on_error():
    raw = _FakeRaw()
    with pytest.raises(ValueError):
        with _PGConnection(raw):
            raise ValueError("boom")
    assert raw.rolledback and raw.closed and not raw.committed
