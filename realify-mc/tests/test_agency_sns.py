"""T-P7-09 SNS signature verification (pure, default suite): reject unsigned/invalid/non-AWS; accept a
properly signed message."""
import base64
import datetime
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.agency import sns      # noqa: E402


def test_rejects_unsigned_and_invalid():
    with pytest.raises(sns.SNSVerificationError):
        sns.verify({"notificationType": "Bounce"})                     # not an SNS envelope
    with pytest.raises(sns.SNSVerificationError):
        sns.verify({"Type": "Notification", "Message": "x", "MessageId": "1", "Timestamp": "t",
                    "TopicArn": "a"})                                   # missing signature
    with pytest.raises(sns.SNSVerificationError):
        sns.verify({"Type": "Notification", "Signature": "abc", "SignatureVersion": "1",
                    "SigningCertURL": "https://evil.example.com/c.pem", "Message": "x",
                    "MessageId": "1", "Timestamp": "t", "TopicArn": "a"})   # non-AWS cert host


def test_accepts_valid_signature():
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subj = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "sns.amazonaws.com")])
    cert = (x509.CertificateBuilder().subject_name(subj).issuer_name(subj)
            .public_key(key.public_key()).serial_number(1)
            .not_valid_before(datetime.datetime(2020, 1, 1))
            .not_valid_after(datetime.datetime(2035, 1, 1)).sign(key, hashes.SHA256()))
    pem = cert.public_bytes(serialization.Encoding.PEM)
    msg = {"Type": "Notification", "Message": "hello", "MessageId": "id1", "Timestamp": "2026-01-01",
           "TopicArn": "arn:aws:sns:us-east-1:1:t", "Subject": "s", "SignatureVersion": "1",
           "SigningCertURL": "https://sns.us-east-1.amazonaws.com/x.pem"}
    sig = key.sign(sns._canonical(msg), padding.PKCS1v15(), hashes.SHA1())
    msg["Signature"] = base64.b64encode(sig).decode()
    assert sns.verify(msg, fetch_cert=lambda: pem) is True


# ---- route-level: /api/ses/notifications is flag-INDEPENDENT (Option A spec change) ----
def _signed(mtype, fields):
    """Build an SNS message of `mtype` signed by a fresh self-signed cert; returns (msg, pem)."""
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subj = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "sns.amazonaws.com")])
    cert = (x509.CertificateBuilder().subject_name(subj).issuer_name(subj)
            .public_key(key.public_key()).serial_number(1)
            .not_valid_before(datetime.datetime(2020, 1, 1))
            .not_valid_after(datetime.datetime(2035, 1, 1)).sign(key, hashes.SHA256()))
    pem = cert.public_bytes(serialization.Encoding.PEM)
    msg = dict(fields, Type=mtype, SignatureVersion="1",
               SigningCertURL="https://sns.us-east-1.amazonaws.com/x.pem")
    sig = key.sign(sns._canonical(msg), padding.PKCS1v15(), hashes.SHA1())
    msg["Signature"] = base64.b64encode(sig).decode()
    return msg, pem


def _client(monkeypatch):
    monkeypatch.setenv("AGENCY_CONSOLE", "off")        # prove the endpoint works with the flag OFF
    from run import make_app
    from fastapi.testclient import TestClient
    return TestClient(make_app())


def test_route_reachable_with_flag_off_but_rejects_bad_signature(monkeypatch):
    # With AGENCY_CONSOLE off this route used to 404; now it must be reachable and reject on signature.
    c = _client(monkeypatch)
    r = c.post("/api/ses/notifications", json={"notificationType": "Bounce"})   # not an SNS envelope
    assert r.status_code == 403 and "verification failed" in r.json()["error"]  # reachable (not 404)
    r = c.post("/api/ses/notifications", json={
        "Type": "Notification", "Signature": "abc", "SignatureVersion": "1",
        "SigningCertURL": "https://evil.example.com/c.pem", "Message": "x",
        "MessageId": "1", "Timestamp": "t", "TopicArn": "a"})                   # non-AWS cert host
    assert r.status_code == 403


def test_route_auto_confirms_subscription_after_signature(monkeypatch):
    c = _client(monkeypatch)
    msg, pem = _signed("SubscriptionConfirmation", {
        "Message": "You have chosen to subscribe", "MessageId": "m1", "Token": "tok-123",
        "Timestamp": "2026-01-01", "TopicArn": "arn:aws:sns:us-east-1:1:ses-feedback",
        "SubscribeURL": "https://sns.us-east-1.amazonaws.com/?Action=ConfirmSubscription&Token=tok-123"})
    visited = {}
    monkeypatch.setattr(sns, "_fetch", lambda url: pem)                 # verify() cert fetch
    monkeypatch.setattr(sns, "_get", lambda url: visited.setdefault("url", url) or 200)  # confirm GET
    r = c.post("/api/ses/notifications", json=msg)
    assert r.status_code == 200 and r.json() == {"ok": True, "confirmed": True}
    assert visited["url"].startswith("https://sns.us-east-1.amazonaws.com/")   # handshake completed, no human
