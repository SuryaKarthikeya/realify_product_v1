"""Envelope crypto (realify/agency/crypto.py) — pure, no DB. Wrap/unwrap, encrypt/decrypt, and AEAD
tamper/wrong-key detection."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.agency import crypto      # noqa: E402


def test_dek_wrap_unwrap_roundtrip():
    dek = crypto.new_dek()
    assert len(dek) == 32
    assert crypto.unwrap_dek(crypto.wrap_dek(dek)) == dek


def test_payload_encrypt_decrypt_roundtrip():
    dek = crypto.new_dek()
    blob = crypto.encrypt(dek, b"ledger payload")
    assert blob != b"ledger payload"                    # actually encrypted
    assert crypto.decrypt(dek, blob) == b"ledger payload"


def test_tampered_ciphertext_fails():
    dek = crypto.new_dek()
    blob = bytearray(crypto.encrypt(dek, b"x"))
    blob[-1] ^= 0x01
    with pytest.raises(Exception):
        crypto.decrypt(dek, bytes(blob))


def test_wrong_dek_cannot_decrypt():
    blob = crypto.encrypt(crypto.new_dek(), b"secret")
    with pytest.raises(Exception):
        crypto.decrypt(crypto.new_dek(), blob)


def test_nonce_is_random_per_call():
    dek = crypto.new_dek()
    assert crypto.encrypt(dek, b"same") != crypto.encrypt(dek, b"same")
