"""T-P0-03: the dev mail driver captures a send to the mailbox for tests to assert on."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import mail          # noqa: E402
from realify.mail import dev      # noqa: E402


def test_dev_driver_captures_send(monkeypatch, tmp_path):
    monkeypatch.setenv("MAIL_DRIVER", "dev")
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path))
    receipt = mail.send("brand@x.com", "Your Realify code", "Code: 123456", reply_to="am@realify.ai")
    assert receipt["driver"] == "dev" and os.path.exists(receipt["path"])
    box = dev.inbox()
    assert len(box) == 1
    m = box[0]
    assert m["to"] == "brand@x.com" and "123456" in m["body"]
    assert m["headers"]["reply_to"] == "am@realify.ai"
    assert dev.inbox(to="nobody@x.com") == []          # recipient filter
    dev.clear()
    assert dev.inbox() == []


def test_two_sends_are_both_captured_in_order(monkeypatch, tmp_path):
    monkeypatch.setenv("MAIL_DRIVER", "dev")
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path))
    mail.send("a@x.com", "one", "first")
    mail.send("a@x.com", "two", "second")
    box = dev.inbox(to="a@x.com")
    assert [m["subject"] for m in box] == ["one", "two"]   # oldest first


def test_unknown_driver_errors(monkeypatch):
    monkeypatch.setenv("MAIL_DRIVER", "carrierpigeon")
    with pytest.raises(ValueError):
        mail.send("a@x.com", "s", "b")
