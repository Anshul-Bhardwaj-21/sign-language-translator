"""
Example: Integrating Authentication Service with Meeting Service

This example demonstrates how to protect Meeting Service endpoints
with JWT authentication and rate limiting.

Requirements: 48.3, 48.4
"""

from fastapi import FastAPI, Depends, HTTPException, status
from auth_service import get_current_user, check_rate_limit, TokenPayload

# Create FastAPI app
app = FastAPI(title="Protected Meeting Service Example")


# ============================================================================
# Example 1: Basic JWT Authentication
# ============================================================================

@app.get("/api/meetings/{meeting_id}")
async def get_meeting_protected(
    meeting_id: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Protected endpoint that requires valid JWT token.
    
    The get_current_user dependency:
    - Extracts JWT token from Authorization header
    - Verifies token signature and expiration
    - Returns user information if valid
    - Raises 401 error if invalid
    """
    return {
        "meeting_id": meeting_id,
        "requested_by": {
            "user_id": current_user.sub,
            "email": current_user.email,
            "name": current_user.name
        },
        "message": "This endpoint is protected by JWT authentication"
    }


# ============================================================================
# Example 2: JWT Authentication + Rate Limiting
# ============================================================================

@app.post("/api/meetings")
async def create_meeting_protected(
    current_user: TokenPayload = Depends(check_rate_limit)
):
    """
    Protected endpoint with JWT authentication AND rate limiting.
    
    The check_rate_limit dependency:
    - Performs all JWT validation (like get_current_user)
    - Additionally checks rate limit (100 requests/minute per user)
    - Raises 429 error if rate limit exceeded
    """
    return {
        "message": "Meeting created successfully",
        "host": {
            "user_id": current_user.sub,
            "email": current_user.email,
            "name": current_user.name
        },
        "note": "This endpoint is protected by JWT auth and rate limiting"
    }


# ============================================================================
# Example 3: Custom Authorization Logic
# ============================================================================

async def verify_host_permission(
    meeting_id: str,
    current_user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """
    Custom dependency that checks if user is the meeting host.
    
    This demonstrates how to build custom authorization logic
    on top of the base JWT authentication.
    """
    # In a real implementation, you would:
    # 1. Query database to get meeting host_id
    # 2. Compare with current_user.sub
    # 3. Raise 403 if not authorized
    
    # Example (simplified):
    # meeting = get_meeting_from_db(meeting_id)
    # if meeting.host_id != current_user.sub:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only the host can perform this action"
    #     )
    
    return current_user


@app.delete("/api/meetings/{meeting_id}")
async def delete_meeting_protected(
    meeting_id: str,
    current_user: TokenPayload = Depends(verify_host_permission)
):
    """
    Protected endpoint that requires user to be the meeting host.
    
    Uses custom authorization dependency that builds on JWT auth.
    """
    return {
        "message": "Meeting deleted successfully",
        "meeting_id": meeting_id,
        "deleted_by": current_user.email
    }


# ============================================================================
# Example 4: Optional Authentication
# ============================================================================

from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth_service import verify_token

security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[TokenPayload]:
    """
    Optional authentication dependency.
    
    Returns user info if valid token provided, None otherwise.
    Useful for endpoints that have different behavior for authenticated users.
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        return verify_token(token, expected_type="access")
    except HTTPException:
        return None


@app.get("/api/meetings/public")
async def get_public_meetings(
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Endpoint that works for both authenticated and anonymous users.
    
    Authenticated users might see additional information.
    """
    if current_user:
        return {
            "meetings": ["meeting1", "meeting2", "meeting3"],
            "user_meetings": ["meeting1"],  # Only shown to authenticated users
            "authenticated": True,
            "user": current_user.email
        }
    else:
        return {
            "meetings": ["meeting1", "meeting2", "meeting3"],
            "authenticated": False,
            "message": "Login to see your meetings"
        }


# ============================================================================
# Example 5: Role-Based Access Control (RBAC)
# ============================================================================

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    HOST = "host"
    PARTICIPANT = "participant"


async def require_role(required_role: UserRole):
    """
    Factory function that creates a dependency for role-based access control.
    
    Usage:
        @app.get("/admin/users")
        async def get_users(user = Depends(require_role(UserRole.ADMIN))):
            ...
    """
    async def role_checker(
        current_user: TokenPayload = Depends(get_current_user)
    ) -> TokenPayload:
        # In a real implementation, you would:
        # 1. Query database to get user's role
        # 2. Compare with required_role
        # 3. Raise 403 if insufficient permissions
        
        # Example (simplified):
        # user_role = get_user_role_from_db(current_user.sub)
        # if user_role != required_role:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail=f"Requires {required_role} role"
        #     )
        
        return current_user
    
    return role_checker


@app.get("/api/admin/analytics")
async def get_analytics(
    current_user: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    """
    Admin-only endpoint.
    
    Requires user to have admin role.
    """
    return {
        "message": "Analytics data",
        "admin": current_user.email,
        "note": "Only admins can access this endpoint"
    }


# ============================================================================
# Example 6: Testing Protected Endpoints
# ============================================================================

"""
To test protected endpoints:

1. Register a user:
   POST http://localhost:8003/api/auth/register
   {
     "email": "test@example.com",
     "name": "Test User",
     "password": "password123"
   }

2. Login to get tokens:
   POST http://localhost:8003/api/auth/login
   {
     "email": "test@example.com",
     "password": "password123"
   }
   
   Response:
   {
     "access_token": "eyJ...",
     "refresh_token": "eyJ...",
     "token_type": "bearer",
     "expires_in": 1800
   }

3. Use access token in requests:
   GET http://localhost:8000/api/meetings/123
   Headers:
     Authorization: Bearer eyJ...

4. Refresh token when expired:
   POST http://localhost:8003/api/auth/refresh
   {
     "refresh_token": "eyJ..."
   }
"""


# ============================================================================
# Example 7: Error Handling
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Custom error handler for authentication errors.
    
    Provides consistent error responses across the API.
    """
    if exc.status_code == 401:
        return {
            "error": "Unauthorized",
            "message": "Invalid or expired token",
            "detail": exc.detail
        }
    elif exc.status_code == 403:
        return {
            "error": "Forbidden",
            "message": "Insufficient permissions",
            "detail": exc.detail
        }
    elif exc.status_code == 429:
        return {
            "error": "Too Many Requests",
            "message": "Rate limit exceeded",
            "detail": exc.detail,
            "retry_after": "60 seconds"
        }
    else:
        return {
            "error": "Error",
            "message": exc.detail
        }


# ============================================================================
# Running the Example
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    Authentication Integration Example
    ==================================
    
    This example demonstrates how to protect endpoints with JWT authentication.
    
    Before running this example:
    1. Start the auth service: python auth_service.py (port 8003)
    2. Ensure PostgreSQL is running with the users table
    
    Then run this example:
    python auth_integration_example.py
    
    The example will start on http://localhost:8000
    
    Try the endpoints:
    - GET  /api/meetings/{id}        - JWT auth required
    - POST /api/meetings              - JWT auth + rate limiting
    - GET  /api/meetings/public       - Optional auth
    - GET  /api/admin/analytics       - Admin role required
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
