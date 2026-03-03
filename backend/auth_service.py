"""
Authentication Service with JWT

Provides JWT-based authentication including:
- JWT token generation with expiration
- JWT token verification middleware
- User login endpoint
- Token refresh endpoint
- Rate limiting middleware

Requirements: 14.4, 48.3, 48.4
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

import psycopg2
from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr
from psycopg2.extras import RealDictCursor
from collections import defaultdict
from time import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter.
    Requirements: 48.4 - 100 requests/minute per user
    """
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if request is allowed for user."""
        now = time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests for user."""
        now = time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(self.requests[user_id]))


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


# ============================================================================
# Pydantic Models
# ============================================================================

class UserCreate(BaseModel):
    """Request model for user registration."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response model for token generation."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str


class UserResponse(BaseModel):
    """Response model for user data."""
    id: str
    email: str
    name: str
    created_at: str


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # user_id
    email: str
    name: str
    exp: int
    iat: int
    type: str  # "access" or "refresh"


# ============================================================================
# Database Connection
# ============================================================================

def get_database_url():
    """Get database URL from environment or use default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db"
    )


def parse_database_url(url: str) -> dict:
    """Parse PostgreSQL URL into connection parameters."""
    url = url.replace("postgresql://", "")
    
    if "@" in url:
        auth, rest = url.split("@", 1)
        user, password = auth.split(":", 1)
    else:
        raise ValueError("Invalid database URL format")
    
    if "/" in rest:
        host_port, dbname = rest.split("/", 1)
    else:
        raise ValueError("Invalid database URL format")
    
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host = host_port
        port = "5432"
    
    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password
    }


def get_db_connection():
    """Create and return a database connection."""
    db_url = get_database_url()
    conn_params = parse_database_url(db_url)
    
    try:
        conn = psycopg2.connect(**conn_params, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )


# ============================================================================
# Password Utilities
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT Token Utilities
# ============================================================================

def create_access_token(user_id: str, email: str, name: str) -> str:
    """
    Create JWT access token with expiration.
    Requirements: 48.3
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def create_refresh_token(user_id: str, email: str, name: str) -> str:
    """
    Create JWT refresh token with longer expiration.
    Requirements: 48.3
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "refresh"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(token: str, expected_type: str = "access") -> TokenPayload:
    """
    Verify JWT token and return payload.
    Requirements: 48.3
    
    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")
    
    Returns:
        TokenPayload with user information
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Validate token type
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}, got {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate required fields
        user_id = payload.get("sub")
        email = payload.get("email")
        name = payload.get("name")
        exp = payload.get("exp")
        iat = payload.get("iat")
        
        if not all([user_id, email, name, exp, iat]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenPayload(
            sub=user_id,
            email=email,
            name=name,
            exp=exp,
            iat=iat,
            type=token_type
        )
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# Authentication Middleware
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenPayload:
    """
    JWT token verification middleware.
    Requirements: 48.3
    
    Extracts and verifies JWT token from Authorization header.
    Returns user information if token is valid.
    """
    token = credentials.credentials
    return verify_token(token, expected_type="access")


async def check_rate_limit(request: Request, current_user: TokenPayload = Depends(get_current_user)):
    """
    Rate limiting middleware.
    Requirements: 48.4 - 100 requests/minute per user
    """
    user_id = current_user.sub
    
    if not rate_limiter.is_allowed(user_id):
        remaining = rate_limiter.get_remaining(user_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 100 requests per minute.",
            headers={
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(time() + 60))
            }
        )
    
    return current_user


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Authentication Service API",
    description="JWT-based authentication service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Authentication Service API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy",
            "service": "auth_service",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "auth_service",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: UserCreate):
    """
    Register a new user.
    
    Creates a new user account with hashed password.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("""
            SELECT id FROM users WHERE email = %s
        """, (request.email,))
        
        existing_user = cursor.fetchone()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash password
        hashed_password = hash_password(request.password)
        
        # Create user
        user_id = str(uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, name, password_hash, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, email, name, created_at
        """, (
            user_id,
            request.email,
            request.name,
            hashed_password,
            datetime.now(timezone.utc)
        ))
        
        user = cursor.fetchone()
        conn.commit()
        
        logger.info(f"User registered: {user['email']}")
        
        return UserResponse(
            id=str(user['id']),
            email=user['email'],
            name=user['name'],
            created_at=user['created_at'].isoformat()
        )
        
    except HTTPException:
        raise
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )
    finally:
        if conn:
            cursor.close()
            conn.close()


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: UserLogin):
    """
    User login endpoint.
    Requirements: 48.3
    
    Authenticates user and returns JWT access and refresh tokens.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user by email
        cursor.execute("""
            SELECT id, email, name, password_hash
            FROM users
            WHERE email = %s
        """, (request.email,))
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(request.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate tokens
        user_id = str(user['id'])
        access_token = create_access_token(user_id, user['email'], user['name'])
        refresh_token = create_refresh_token(user_id, user['email'], user['name'])
        
        logger.info(f"User logged in: {user['email']}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )
    finally:
        if conn:
            cursor.close()
            conn.close()


@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: TokenRefreshRequest):
    """
    Token refresh endpoint.
    Requirements: 48.3
    
    Accepts a refresh token and returns new access and refresh tokens.
    """
    try:
        # Verify refresh token
        payload = verify_token(request.refresh_token, expected_type="refresh")
        
        # Generate new tokens
        access_token = create_access_token(payload.sub, payload.email, payload.name)
        refresh_token = create_refresh_token(payload.sub, payload.email, payload.name)
        
        logger.info(f"Token refreshed for user: {payload.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenPayload = Depends(get_current_user)):
    """
    Get current user information.
    Requirements: 48.3
    
    Returns user information from JWT token.
    Requires valid access token.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get full user information from database
        cursor.execute("""
            SELECT id, email, name, created_at
            FROM users
            WHERE id = %s
        """, (current_user.sub,))
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=str(user['id']),
            email=user['email'],
            name=user['name'],
            created_at=user['created_at'].isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )
    finally:
        if conn:
            cursor.close()
            conn.close()


@app.get("/api/auth/verify")
async def verify_token_endpoint(current_user: TokenPayload = Depends(get_current_user)):
    """
    Verify token endpoint.
    Requirements: 48.3
    
    Verifies if the provided token is valid.
    Returns user information if valid.
    """
    return {
        "valid": True,
        "user_id": current_user.sub,
        "email": current_user.email,
        "name": current_user.name,
        "expires_at": datetime.fromtimestamp(current_user.exp, tz=timezone.utc).isoformat()
    }


@app.get("/api/protected/example")
async def protected_endpoint(current_user: TokenPayload = Depends(check_rate_limit)):
    """
    Example protected endpoint with rate limiting.
    Requirements: 48.3, 48.4
    
    Demonstrates JWT authentication and rate limiting.
    """
    remaining = rate_limiter.get_remaining(current_user.sub)
    
    return {
        "message": "This is a protected endpoint",
        "user_id": current_user.sub,
        "email": current_user.email,
        "rate_limit": {
            "limit": 100,
            "remaining": remaining,
            "window": "60 seconds"
        }
    }


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
