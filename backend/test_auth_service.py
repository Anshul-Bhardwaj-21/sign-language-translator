"""
Unit tests for Authentication Service

Tests JWT token generation, verification, login, refresh, and rate limiting.
Requirements: 48.3, 48.4
"""

import pytest
import time
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from jose import jwt

from auth_service import (
    app,
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
    RateLimiter,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


# Test client
client = TestClient(app)


# ============================================================================
# Password Hashing Tests
# ============================================================================

def test_hash_password():
    """Test password hashing."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 0
    assert hashed.startswith("$2b$")  # bcrypt prefix


def test_verify_password_correct():
    """Test password verification with correct password."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password."""
    password = "test_password_123"
    wrong_password = "wrong_password"
    hashed = hash_password(password)
    
    assert verify_password(wrong_password, hashed) is False


# ============================================================================
# JWT Token Generation Tests
# ============================================================================

def test_create_access_token():
    """Test access token generation."""
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    token = create_access_token(user_id, email, name)
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Decode and verify payload
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert payload["name"] == name
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_create_refresh_token():
    """Test refresh token generation."""
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    token = create_refresh_token(user_id, email, name)
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Decode and verify payload
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert payload["name"] == name
    assert payload["type"] == "refresh"
    assert "exp" in payload
    assert "iat" in payload


def test_access_token_expiration():
    """Test that access token has correct expiration time."""
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    before = datetime.now(timezone.utc)
    token = create_access_token(user_id, email, name)
    after = datetime.now(timezone.utc)
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    
    # Check expiration is approximately ACCESS_TOKEN_EXPIRE_MINUTES from now
    expected_exp = before + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    time_diff = abs((exp_time - expected_exp).total_seconds())
    
    assert time_diff < 5  # Within 5 seconds tolerance


# ============================================================================
# JWT Token Verification Tests
# ============================================================================

def test_verify_valid_access_token():
    """Test verification of valid access token."""
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    token = create_access_token(user_id, email, name)
    payload = verify_token(token, expected_type="access")
    
    assert payload.sub == user_id
    assert payload.email == email
    assert payload.name == name
    assert payload.type == "access"


def test_verify_valid_refresh_token():
    """Test verification of valid refresh token."""
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    token = create_refresh_token(user_id, email, name)
    payload = verify_token(token, expected_type="refresh")
    
    assert payload.sub == user_id
    assert payload.email == email
    assert payload.name == name
    assert payload.type == "refresh"


def test_verify_token_wrong_type():
    """Test that verification fails when token type doesn't match."""
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    access_token = create_access_token(user_id, email, name)
    
    with pytest.raises(Exception) as exc_info:
        verify_token(access_token, expected_type="refresh")
    
    assert exc_info.value.status_code == 401


def test_verify_invalid_token():
    """Test verification of invalid token."""
    invalid_token = "invalid.token.here"
    
    with pytest.raises(Exception) as exc_info:
        verify_token(invalid_token, expected_type="access")
    
    assert exc_info.value.status_code == 401


def test_verify_expired_token():
    """Test verification of expired token."""
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    # Create token that expired 1 hour ago
    now = datetime.now(timezone.utc)
    exp = now - timedelta(hours=1)
    
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "exp": int(exp.timestamp()),
        "iat": int((now - timedelta(hours=2)).timestamp()),
        "type": "access"
    }
    
    expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    with pytest.raises(Exception) as exc_info:
        verify_token(expired_token, expected_type="access")
    
    assert exc_info.value.status_code == 401


# ============================================================================
# Rate Limiter Tests
# ============================================================================

def test_rate_limiter_allows_requests_within_limit():
    """Test that rate limiter allows requests within limit."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    user_id = "test-user"
    
    # Should allow first 5 requests
    for i in range(5):
        assert limiter.is_allowed(user_id) is True


def test_rate_limiter_blocks_requests_over_limit():
    """Test that rate limiter blocks requests over limit."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    user_id = "test-user"
    
    # Use up the limit
    for i in range(5):
        limiter.is_allowed(user_id)
    
    # Next request should be blocked
    assert limiter.is_allowed(user_id) is False


def test_rate_limiter_resets_after_window():
    """Test that rate limiter resets after time window."""
    limiter = RateLimiter(max_requests=2, window_seconds=1)
    user_id = "test-user"
    
    # Use up the limit
    assert limiter.is_allowed(user_id) is True
    assert limiter.is_allowed(user_id) is True
    assert limiter.is_allowed(user_id) is False
    
    # Wait for window to expire
    time.sleep(1.1)
    
    # Should allow requests again
    assert limiter.is_allowed(user_id) is True


def test_rate_limiter_per_user():
    """Test that rate limiter is per-user."""
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    user1 = "user-1"
    user2 = "user-2"
    
    # User 1 uses up their limit
    assert limiter.is_allowed(user1) is True
    assert limiter.is_allowed(user1) is True
    assert limiter.is_allowed(user1) is False
    
    # User 2 should still have their full limit
    assert limiter.is_allowed(user2) is True
    assert limiter.is_allowed(user2) is True
    assert limiter.is_allowed(user2) is False


def test_rate_limiter_get_remaining():
    """Test getting remaining requests."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    user_id = "test-user"
    
    assert limiter.get_remaining(user_id) == 5
    
    limiter.is_allowed(user_id)
    assert limiter.get_remaining(user_id) == 4
    
    limiter.is_allowed(user_id)
    assert limiter.get_remaining(user_id) == 3


# ============================================================================
# API Endpoint Tests
# ============================================================================

def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Authentication Service API"
    assert data["status"] == "running"


@patch('auth_service.get_db_connection')
def test_health_check_healthy(mock_db):
    """Test health check when database is connected."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_db.return_value = mock_conn
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@patch('auth_service.get_db_connection')
def test_register_user_success(mock_db):
    """Test successful user registration."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_db.return_value = mock_conn
    
    # Mock no existing user
    mock_cursor.fetchone.side_effect = [
        None,  # No existing user
        {  # New user created
            'id': 'test-user-id',
            'email': 'test@example.com',
            'name': 'Test User',
            'created_at': datetime.now(timezone.utc)
        }
    ]
    
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "name": "Test User",
        "password": "password123"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data


@patch('auth_service.get_db_connection')
def test_register_user_duplicate_email(mock_db):
    """Test registration with duplicate email."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_db.return_value = mock_conn
    
    # Mock existing user
    mock_cursor.fetchone.return_value = {'id': 'existing-user-id'}
    
    response = client.post("/api/auth/register", json={
        "email": "existing@example.com",
        "name": "Test User",
        "password": "password123"
    })
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@patch('auth_service.get_db_connection')
def test_login_success(mock_db):
    """Test successful login."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_db.return_value = mock_conn
    
    # Mock user with hashed password
    password = "password123"
    hashed = hash_password(password)
    
    mock_cursor.fetchone.return_value = {
        'id': 'test-user-id',
        'email': 'test@example.com',
        'name': 'Test User',
        'password_hash': hashed
    }
    
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": password
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == ACCESS_TOKEN_EXPIRE_MINUTES * 60


@patch('auth_service.get_db_connection')
def test_login_invalid_email(mock_db):
    """Test login with invalid email."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_db.return_value = mock_conn
    
    # Mock no user found
    mock_cursor.fetchone.return_value = None
    
    response = client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "password123"
    })
    
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@patch('auth_service.get_db_connection')
def test_login_invalid_password(mock_db):
    """Test login with invalid password."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_db.return_value = mock_conn
    
    # Mock user with different password
    correct_password = "correct_password"
    hashed = hash_password(correct_password)
    
    mock_cursor.fetchone.return_value = {
        'id': 'test-user-id',
        'email': 'test@example.com',
        'name': 'Test User',
        'password_hash': hashed
    }
    
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrong_password"
    })
    
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_refresh_token_success():
    """Test successful token refresh."""
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    refresh_token = create_refresh_token(user_id, email, name)
    
    response = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_with_access_token():
    """Test that refresh fails when using access token."""
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    access_token = create_access_token(user_id, email, name)
    
    response = client.post("/api/auth/refresh", json={
        "refresh_token": access_token
    })
    
    assert response.status_code == 401


@patch('auth_service.get_db_connection')
def test_get_current_user_info(mock_db):
    """Test getting current user info with valid token."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_db.return_value = mock_conn
    
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    mock_cursor.fetchone.return_value = {
        'id': user_id,
        'email': email,
        'name': name,
        'created_at': datetime.now(timezone.utc)
    }
    
    access_token = create_access_token(user_id, email, name)
    
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["name"] == name


def test_get_current_user_info_no_token():
    """Test getting user info without token."""
    response = client.get("/api/auth/me")
    # FastAPI returns 401 when no credentials are provided
    assert response.status_code == 401


def test_verify_token_endpoint():
    """Test token verification endpoint."""
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    access_token = create_access_token(user_id, email, name)
    
    response = client.get(
        "/api/auth/verify",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["user_id"] == user_id
    assert data["email"] == email


def test_protected_endpoint_with_valid_token():
    """Test protected endpoint with valid token."""
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    
    access_token = create_access_token(user_id, email, name)
    
    response = client.get(
        "/api/protected/example",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert "rate_limit" in data


def test_protected_endpoint_without_token():
    """Test protected endpoint without token."""
    response = client.get("/api/protected/example")
    # FastAPI returns 401 when no credentials are provided
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
