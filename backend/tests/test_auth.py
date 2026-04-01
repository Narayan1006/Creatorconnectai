"""Tests for JWT authentication middleware and role-based access control."""
from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.core.auth import (
    create_access_token,
    decode_access_token,
    require_role,
)


def test_create_and_decode_token():
    payload = {"sub": "user123", "role": "business"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "user123"
    assert decoded["role"] == "business"
    assert "exp" in decoded


def test_decode_expired_token():
    token = create_access_token({"sub": "u1", "role": "creator"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_decode_malformed_token():
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not.a.valid.token")
    assert exc_info.value.status_code == 401
    assert "invalid" in exc_info.value.detail.lower()


def test_require_role_passes_correct_role():
    dep = require_role("business")
    user = {"sub": "u1", "role": "business"}
    result = dep(current_user=user)
    assert result == user


def test_require_role_raises_403_on_wrong_role():
    dep = require_role("business")
    user = {"sub": "u2", "role": "creator"}
    with pytest.raises(HTTPException) as exc_info:
        dep(current_user=user)
    assert exc_info.value.status_code == 403


def test_require_role_raises_403_on_missing_role():
    dep = require_role("creator")
    user = {"sub": "u3"}
    with pytest.raises(HTTPException) as exc_info:
        dep(current_user=user)
    assert exc_info.value.status_code == 403


def test_token_payload_includes_required_fields():
    token = create_access_token({"sub": "u1", "role": "creator"})
    decoded = decode_access_token(token)
    assert "sub" in decoded
    assert "role" in decoded
    assert "exp" in decoded
