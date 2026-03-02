# Development Setup Guide

This guide will help you set up the development environment for the Advanced Meeting Features project.

## Prerequisites

- **Docker & Docker Compose** (v20.10+)
- **Node.js** (v20+)
- **Python** (v3.11+)
- **Git**

## Quick Start with Docker

The easiest way to get started is using Docker Compose:

```bash
# 1. Clone the repository
git clone <repository-url>
cd <repository-name>

# 2. Copy environment files
cp .env.example .env
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env

# 3. Start all services
docker-compose up -d

# 4. Check service health
docker-compose ps

# 5. View logs
docker-compose logs -f
```

Services will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8001
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Manual Setup (Without Docker)

### 1. Database Setup

**PostgreSQL:**
```bash
# Install PostgreSQL 15
# Create database and user
psql -U postgres
CREATE DATABASE meeting_db;
CREATE USER meeting_user WITH PASSWORD 'meeting_pass';
GRANT ALL PRIVILEGES ON DATABASE meeting_db TO meeting_user;
\q
```

**Redis:**
```bash
# Install Redis 7
# Start Redis server
redis-server
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your database credentials
# DATABASE_URL=postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db
# REDIS_URL=redis://localhost:6379

# Run database migrations (when available)
# alembic upgrade head

# Start the backend server
uvicorn simple_server:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your backend URL
# VITE_API_URL=http://localhost:8001
# VITE_WS_URL=ws://localhost:8001

# Start the development server
npm run dev
```

## Development Tools

### Pre-commit Hooks

Install pre-commit hooks to automatically format and lint code:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Code Formatting

**Backend (Python):**
```bash
cd backend

# Format with Black
black .

# Sort imports with isort
isort .

# Lint with flake8
flake8 .
```

**Frontend (TypeScript/React):**
```bash
cd frontend

# Format with Prettier
npm run format

# Lint with ESLint
npm run lint

# Fix linting issues
npm run lint -- --fix
```

### Running Tests

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend

# Run tests once
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui
```

## Project Structure

```
.
├── backend/                 # Python FastAPI backend
│   ├── models/             # Database models
│   ├── services/           # Business logic
│   ├── api/                # API routes
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Backend Docker image
│   └── .env.example        # Backend environment template
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── contexts/      # React contexts
│   │   ├── hooks/         # Custom hooks
│   │   └── utils/         # Utility functions
│   ├── package.json       # Node dependencies
│   ├── Dockerfile         # Frontend Docker image
│   └── .env.example       # Frontend environment template
├── ml/                    # Machine learning code
│   ├── models/            # ML model definitions
│   ├── training/          # Training scripts
│   └── inference/         # Inference code
├── docker-compose.yml     # Docker Compose configuration
├── .env.example           # Root environment template
└── .pre-commit-config.yaml # Pre-commit hooks config
```

## Environment Variables

### Backend (.env)

Key variables to configure:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret key for JWT tokens (generate with `openssl rand -hex 32`)
- `CORS_ORIGINS`: Allowed CORS origins
- `STORAGE_PROVIDER`: Cloud storage provider (s3, gcs, or local)

### Frontend (.env)

Key variables to configure:
- `VITE_API_URL`: Backend API URL
- `VITE_WS_URL`: WebSocket URL
- `VITE_ENABLE_*`: Feature flags

## Common Tasks

### Reset Database

```bash
# With Docker
docker-compose down -v
docker-compose up -d postgres

# Manual
dropdb meeting_db
createdb meeting_db
# Run migrations
```

### Clear Redis Cache

```bash
# With Docker
docker-compose exec redis redis-cli FLUSHALL

# Manual
redis-cli FLUSHALL
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Rebuild Docker Images

```bash
# Rebuild all
docker-compose build

# Rebuild specific service
docker-compose build backend
docker-compose build frontend

# Rebuild and restart
docker-compose up -d --build
```

## Troubleshooting

### Port Already in Use

If ports 5173, 8001, 5432, or 6379 are already in use:

1. Stop the conflicting service
2. Or modify ports in `docker-compose.yml`

### Database Connection Issues

1. Check PostgreSQL is running: `docker-compose ps postgres`
2. Verify credentials in `.env`
3. Check database exists: `docker-compose exec postgres psql -U meeting_user -d meeting_db`

### Frontend Not Loading

1. Check backend is running: `curl http://localhost:8001/health`
2. Verify CORS origins in backend `.env`
3. Check browser console for errors

### Module Not Found Errors

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

1. Review the [Requirements Document](.kiro/specs/advanced-meeting-features/requirements.md)
2. Review the [Design Document](.kiro/specs/advanced-meeting-features/design.md)
3. Check the [Implementation Tasks](.kiro/specs/advanced-meeting-features/tasks.md)
4. Start implementing features!

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [WebRTC Documentation](https://webrtc.org/)
- [Socket.IO Documentation](https://socket.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/docs/)
