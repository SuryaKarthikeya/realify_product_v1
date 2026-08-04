"""Envelope encryption for the agency console (agency-plan P1). Each brand gets a random 256-bit DEK;
the DEK is wrapped (encrypted) by a master KEK and stored in brand_keys.wrapped_dek. Ledger payloads
are AES-256-GCM encrypted with the brand's DEK. Crypto-shred = destroy the wrapped DEK (set NULL):
the DEK becomes unrecoverable, so every payload for that brand is permanently unreadable — while the
ledger hash chain (computed over ciphertext) still verifies.

KEK source: env MASTER_KEK (base64 of exactly 32 bytes) in prod; a fixed, clearly-marked dev key
otherwise. All AEAD, so tampering with any wrapped key or payload fails loudly on open.
"""
import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_NONCE = 12


def _kek():
    b64 = os.environ.get("MASTER_KEK")
    if b64:
        k = base64.b64decode(b64)
        if len(k) != 32:
            raise ValueError("MASTER_KEK must be base64 of exactly 32 bytes")
        return k
    # DEV ONLY: deterministic key so dev/test can wrap/unwrap without config. Never used when
    # MASTER_KEK is set (prod/staging must set it).
    return hashlib.sha256(b"realify-agency-dev-kek").digest()


def _seal(key, plaintext):
    nonce = os.urandom(_NONCE)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, None)


def _open(key, blob):
    blob = bytes(blob)
    return AESGCM(key).decrypt(blob[:_NONCE], blob[_NONCE:], None)


def kek_fingerprint():
    """Non-secret, stable id of the CURRENT KEK. Lets ops confirm which KEK is active and lets us
    detect a brand key wrapped under a DIFFERENT KEK — without exposing key material."""
    return hashlib.sha256(b"realify-kek-fp:" + _kek()).hexdigest()[:16]


def new_dek():
    return AESGCM.generate_key(bit_length=256)


def wrap_dek(dek):
    return _seal(_kek(), dek)


def unwrap_dek(wrapped):
    return _open(_kek(), wrapped)


def encrypt(dek, plaintext):
    """Encrypt bytes with a brand DEK -> nonce||ciphertext (AES-256-GCM)."""
    return _seal(dek, plaintext)


def decrypt(dek, blob):
    """Decrypt nonce||ciphertext with a brand DEK. Raises on tamper/wrong key."""
    return _open(dek, blob)
