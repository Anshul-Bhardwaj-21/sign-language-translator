-- Migration: Add password_hash field to users table
-- Requirements: 48.3 - JWT token-based authentication

-- Add password_hash column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- Create index on email for faster lookups during authentication
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
