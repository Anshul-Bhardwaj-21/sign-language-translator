# Authentication Service

JWT-based authentication service for the Advanced Meeting Features platform.

## Features

- **JWT Token Generation**: Creates access and refresh tokens with configurable expiration
- **Token Verification**: Middleware for validating JWT tokens
- **User Registration**: Secure user registration with password hashing
- **User Login**: Email/password authentication
- **Token Refresh**: Refresh access tokens using refresh tokens
- **Rate Limiting**: 100 requests per minute per user (configurable)
- **Password Security**: Bcrypt password hashing

## Requirements

Implements requirements:
- **14.4**: Encrypted signaling data using TLS 1.3
- **48.3**: JWT token-based authentication
- **48.4**: Rate limiting (100 requests/minute per user)

## API Endpoints

### Public Endpoints

#### POST /api/auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword123"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### POST /api/auth/login
Authenticate and receive JWT tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /api/auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Protected Endpoints

All protected endpoints require an `Authorization` header:
```
Authorization: Bearer <access_token>
```

#### GET /api/auth/me
Get current user information.

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### GET /api/auth/verify
Verify if token is valid.

**Response (200):**
```json
{
  "valid": true,
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "expires_at": "2024-01-01T00:30:00Z"
}
```

#### GET /api/protected/example
Example protected endpoint with rate limiting.

**Response (200):**
```json
{
  "message": "This is a protected endpoint",
  "user_id": "uuid",
  "email": "user@example.com",
  "rate_limit": {
    "limit": 100,
    "remaining": 95,
    "window": "60 seconds"
  }
}
```

## Configuration

Environment variables:

- `JWT_SECRET_KEY`: Secret key for JWT signing (default: "your-secret-key-change-in-production")
- `DATABASE_URL`: PostgreSQL connection string
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiration in minutes (default: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration in days (default: 7)

## Token Structure

### Access Token Payload
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "name": "John Doe",
  "exp": 1234567890,
  "iat": 1234567890,
  "type": "access"
}
```

### Refresh Token Payload
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "name": "John Doe",
  "exp": 1234567890,
  "iat": 1234567890,
  "type": "refresh"
}
```

## Rate Limiting

The service implements per-user rate limiting:
- **Limit**: 100 requests per minute per user
- **Window**: 60 seconds rolling window
- **Response**: HTTP 429 when limit exceeded
- **Headers**: 
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Unix timestamp when window resets

## Security Features

1. **Password Hashing**: Bcrypt with automatic salt generation
2. **JWT Signing**: HS256 algorithm with secret key
3. **Token Expiration**: Automatic expiration for access and refresh tokens
4. **Token Type Validation**: Ensures correct token type for each endpoint
5. **Rate Limiting**: Prevents abuse and brute force attacks
6. **CORS**: Configured for specific origins only

## Database Schema

The service requires a `users` table with the following structure:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_users_email ON users(email);
```

## Running the Service

### Development
```bash
cd backend
python auth_service.py
```

The service will start on `http://0.0.0.0:8003`

### Production
Use a production WSGI server like Gunicorn:
```bash
gunicorn auth_service:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8003
```

## Testing

Run the test suite:
```bash
pytest backend/test_auth_service.py -v
```

Test coverage includes:
- JWT token generation and verification
- Password hashing and verification
- Rate limiting functionality
- All API endpoints
- Error handling

## Integration with Meeting Service

To protect Meeting Service endpoints, use the authentication middleware:

```python
from auth_service import get_current_user, check_rate_limit
from fastapi import Depends

@app.get("/api/meetings/{meeting_id}")
async def get_meeting(
    meeting_id: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    # current_user contains validated user information
    # Implement endpoint logic
    pass

@app.post("/api/meetings")
async def create_meeting(
    request: CreateMeetingRequest,
    current_user: TokenPayload = Depends(check_rate_limit)
):
    # Rate limiting is automatically applied
    # Implement endpoint logic
    pass
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "User with this email already exists"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Maximum 100 requests per minute."
}
```

### 503 Service Unavailable
```json
{
  "detail": "Database connection failed"
}
```

## Known Issues

- **Python 3.14 Compatibility**: There's a known compatibility issue with the bcrypt library and Python 3.14. The service works correctly, but some unit tests may fail. This will be resolved when bcrypt releases a Python 3.14-compatible version.

## Future Enhancements

- OAuth2 integration (Google, GitHub, etc.)
- Multi-factor authentication (MFA)
- Password reset functionality
- Email verification
- Session management
- Audit logging
- IP-based rate limiting
- Distributed rate limiting with Redis
