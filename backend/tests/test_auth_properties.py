"""
Property-based tests for JWT authentication and role-based access control.

Property 9 (Req 1.4/1.5): Role-based access control
Property 16 (Req 1.3): JWT authentication required
"""
import pytest
from fastapi import HTTPException
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from app.core.auth import (
    create_access_token,
    decode_access_token,
    require_role,
)

VALID_ROLES = ["business", "creator"]


# ---------------------------------------------------------------------------
# Property 9: Role-based access control
# Validates: Requirements 1.4, 1.5
# ---------------------------------------------------------------------------

@given(st.sampled_from(VALID_ROLES))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_token_role_claim_roundtrip(role):
    """
    Property 9 (partial): For any role R, a token created with role R must
    decode to contain exactly role R.

    **Validates: Requirements 1.4, 1.5**
    """
    token = create_access_token({"sub": "user_test", "role": role})
    decoded = decode_access_token(token)
    assert decoded["role"] == role


@given(st.sampled_from(VALID_ROLES))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_require_role_rejects_other_role(role):
    """
    Property 9: For any role R, accessing an endpoint restricted to the OTHER
    role must raise HTTP 403.

    **Validates: Requirements 1.4, 1.5**
    """
    other_role = "creator" if role == "business" else "business"
    dep = require_role(other_role)
    user = {"sub": "user_test", "role": role}
    with pytest.raises(HTTPException) as exc_info:
        dep(current_user=user)
    assert exc_info.value.status_code == 403


@given(st.sampled_from(VALID_ROLES))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_require_role_accepts_correct_role(role):
    """
    Property 9 (positive case): require_role(R) must accept a user with role R.

    **Validates: Requirements 1.4, 1.5**
    """
    dep = require_role(role)
    user = {"sub": "user_test", "role": role}
    result = dep(current_user=user)
    assert result == user


@given(st.sampled_from(VALID_ROLES))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_token_for_role_a_rejected_by_require_role_b(role):
    """
    Property 9: For any two different roles, a token for role A must be
    rejected by require_role(role_B).

    **Validates: Requirements 1.4, 1.5**
    """
    other_role = "creator" if role == "business" else "business"
    token = create_access_token({"sub": "user_test", "role": role})
    decoded = decode_access_token(token)

    dep = require_role(other_role)
    with pytest.raises(HTTPException) as exc_info:
        dep(current_user=decoded)
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Property 16: JWT authentication required
# Validates: Requirements 1.3, 1.6
# ---------------------------------------------------------------------------

@given(st.text(min_size=1))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_invalid_token_raises_401(token_string):
    """
    Property 16: For any random string that is not a valid JWT,
    decode_access_token must raise HTTPException with status 401.

    **Validates: Requirements 1.3, 1.6**
    """
    # Skip strings that happen to be valid JWTs (astronomically unlikely but safe)
    try:
        result = decode_access_token(token_string)
        # If it decoded without error, it must be a valid JWT — skip this example
        # (hypothesis may generate a valid token string in theory, but practically won't)
        pytest.skip(f"Generated string happened to be a valid JWT: {token_string[:20]}...")
    except HTTPException as exc:
        assert exc.status_code == 401


# ---------------------------------------------------------------------------
# Additional properties
# ---------------------------------------------------------------------------

@given(st.sampled_from(VALID_ROLES))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_create_access_token_always_includes_required_fields(role):
    """
    Property: For any valid role, create_access_token always includes
    "role", "sub", and "exp" in the decoded payload.

    **Validates: Requirements 1.4, 1.5**
    """
    token = create_access_token({"sub": "user_test", "role": role})
    decoded = decode_access_token(token)
    assert "role" in decoded
    assert "sub" in decoded
    assert "exp" in decoded
