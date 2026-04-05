# Sign Language Video Call Application

[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci-cd.yml)
[![Backend Tests](https://img.shields.io/badge/backend-tests-passing-brightgreen)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions)
[![Frontend Tests](https://img.shields.io/badge/frontend-tests-passing-brightgreen)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A real-time video calling application with ASL (American Sign Language) recognition, live captioning, and advanced meeting features. Built with React, FastAPI, WebRTC, PostgreSQL, and Redis.

## 📑 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Environment Configuration](#environment-configuration)
- [Development Workflow](#development-workflow)
- [CI/CD Pipeline](#cicd-pipeline)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This application enables real-time video communication with integrated sign language recognition and live captioning. It's designed to make video calls more accessible for deaf and hard-of-hearing users by providing real-time ASL recognition, text-to-speech, and comprehensive meeting features.

### Key Capabilities

- **Real-time Video Calling**: WebRTC-based peer-to-peer video communication
- **ASL Recognition**: Live sign language detection with confidence scores
- **Live Captions**: Real-time caption display with text-to-speech
- **Meeting Management**: Create, join, and manage video meetings
- **Recording & Transcription**: Record meetings with automatic transcription
- **Advanced Features**: Screen sharing, breakout rooms, waiting rooms
- **Accessibility**: Full keyboard navigation and accessibility mode

## ✨ Features

### Core Features (Implemented)

- ✅ **WebRTC Video Calling** - Peer-to-peer video between multiple users
- ✅ **WebSocket Signaling** - Real-time connection establishment with Socket.IO
- ✅ **Mock ASL Recognition** - Deterministic gesture detection (offline mode)
- ✅ **Live Captions** - Real-time caption display with confidence scores
- ✅ **Text-to-Speech** - Browser-based TTS for caption reading
- ✅ **Chat System** - Text messaging between participants
- ✅ **Camera Controls** - Reliable camera on/off functionality
- ✅ **Accessibility Mode** - Toggle ASL recognition on/off
- ✅ **Keyboard Shortcuts** - Full keyboard navigation support
- ✅ **Meeting Management** - Create, join, and manage meetings
- ✅ **Participant Management** - Track and manage meeting participants
- ✅ **Authentication** - JWT-based user authentication
- ✅ **Database Integration** - PostgreSQL for persistent storage
- ✅ **Redis Caching** - Session state and frame buffering
- ✅ **Cloud Storage** - AWS S3/GCS integration for recordings

### Advanced Features (Planned)

- 🔄 **Real ASL Model** - Train and deploy production ASL models
- 🔄 **Recording Service** - Record and store meeting sessions
- 🔄 **Transcription Service** - Automatic speech-to-text transcription
- 🔄 **AI Summaries** - Generate meeting summaries with AI
- 🔄 **Breakout Rooms** - Split meetings into smaller groups
- 🔄 **Waiting Room** - Host-controlled participant admission
- 🔄 **Screen Sharing** - Share screen with participants
- 🔄 **Calendar Integration** - Google Calendar and Outlook sync

### Mock Inference Mode

The app uses **mock ASL inference** by default (no external AI APIs required):
- Deterministic predictions based on hand geometry
- Works completely offline
- No API keys needed
- Suitable for demos and development

To use real ASL models, see ML training documentation in `ml/` directory.

## 🚀 Quick Start

Choose one of three methods to run the application:

### Method 1: Docker Compose (Recommended)

**Prerequisites**: Docker and Docker Compose installed

```bash
# 1. Clone the repository
git clone <repository-url>
cd sign-language-translator

# 2. Copy environment files
cp .env.example .env
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env

# 3. Start all services
docker-compose up -d

# 4. Check service health
docker-compose ps

# 5. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8001
```

### Method 2: Quick Start Scripts

**Windows:**
```powershell
# Backend (Terminal 1)
cd backend
.\run-dev.ps1

# Frontend (Terminal 2)
cd frontend
.\run-dev.ps1
```

**Linux/Mac:**
```bash
# Backend (Terminal 1)
cd backend
chmod +x run-dev.sh
./run-dev.sh

# Frontend (Terminal 2)
cd frontend
chmod +x run-dev.sh
./run-dev.sh
```

### Method 3: Manual Setup

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python simple_server.py
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

### Testing the Application

1. Open **TWO browser tabs** (Chrome/Edge recommended):
   - Tab A: http://localhost:5173
   - Tab B: http://localhost:5173

2. **Tab A** (Host):
   - Click "Create Room"
   - Copy the room code (e.g., "ABC123")
   - Enable camera when prompted
   - Turn ON "Accessibility Mode" (🧏 button)

3. **Tab B** (Guest):
   - Click "Join Room"
   - Paste the room code
   - Click "Join"
   - Enable camera when prompted

4. **Test Features**:
   - ✅ Both tabs should see each other's video
   - ✅ Wave your hand in Tab A → Tab B sees mock captions
   - ✅ Type in chat → messages appear in both tabs
   - ✅ Click speaker icon → browser TTS reads captions

## 🛠️ Technology Stack

### Frontend
- **React** 18.2.0 - UI framework
- **TypeScript** 5.9.3 - Type-safe JavaScript
- **Vite** 5.0.8 - Build tool and dev server
- **Tailwind CSS** 3.4.0 - Utility-first CSS framework
- **React Router** 6.21.0 - Client-side routing
- **Socket.IO Client** 4.6.0 - Real-time communication
- **Vitest** 4.0.18 - Testing framework
- **ESLint & Prettier** - Code quality and formatting

### Backend
- **FastAPI** - Modern Python web framework
- **Python** 3.11+ - Programming language
- **Socket.IO** - WebSocket server for signaling
- **Uvicorn** - ASGI server
- **PostgreSQL** 15 - Relational database
- **Redis** 7 - In-memory cache and session store
- **SQLAlchemy** - ORM (optional)
- **Pydantic** - Data validation
- **pytest** - Testing framework

### Infrastructure
- **Docker** & **Docker Compose** - Containerization
- **GitHub Actions** - CI/CD pipeline
- **Nginx** - Reverse proxy and load balancer
- **AWS S3 / Google Cloud Storage** - Cloud storage for recordings

### ML/AI (Optional)
- **PyTorch** - Deep learning framework
- **OpenCV** - Computer vision
- **MediaPipe** - Hand landmark detection
- **MLflow** - Experiment tracking
- **NumPy** - Numerical computing

### Development Tools
- **Black** - Python code formatter
- **isort** - Python import sorter
- **flake8** - Python linter
- **pre-commit** - Git hooks for code quality
- **Makefile** - Task automation

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   React UI   │  │   WebRTC     │  │  Socket.IO   │         │
│  │   (Vite)     │  │   (P2P)      │  │   Client     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          │ HTTP/REST        │ WebRTC           │ WebSocket
          │                  │ (Video/Audio)    │ (Signaling)
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend Services                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   FastAPI    │  │  Signaling   │  │     Auth     │         │
│  │   REST API   │  │   Server     │  │   Service    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                 │
│                            │                                     │
│         ┌──────────────────┴──────────────────┐                │
│         ▼                                      ▼                 │
│  ┌──────────────┐                      ┌──────────────┐        │
│  │  PostgreSQL  │                      │    Redis     │        │
│  │  (Meetings,  │                      │  (Sessions,  │        │
│  │   Users,     │                      │   Frames,    │        │
│  │   Records)   │                      │   Cache)     │        │
│  └──────────────┘                      └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
          │                                      │
          ▼                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   AWS S3 /   │  │  Mock ASL    │  │   MLflow     │         │
│  │     GCS      │  │  Inference   │  │  (Optional)  │         │
│  │ (Recordings) │  │   Engine     │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Authentication**: JWT tokens via Auth Service
2. **Meeting Creation**: REST API creates meeting in PostgreSQL
3. **WebRTC Signaling**: Socket.IO exchanges SDP offers/answers
4. **Video Streaming**: Peer-to-peer WebRTC connections
5. **Frame Capture**: Frontend captures frames → Backend inference
6. **Caption Display**: Inference results → WebSocket → Frontend
7. **Session State**: Redis stores active sessions and frame buffers
8. **Recording Storage**: Recordings uploaded to S3/GCS

## 📁 Project Structure

```
sign-language-translator/
├── backend/                          # Python FastAPI backend
│   ├── database/                     # Database schema and migrations
│   │   ├── schema.sql               # PostgreSQL schema
│   │   ├── init_db.py               # Database initialization
│   │   ├── test_schema.py           # Schema validation tests
│   │   └── test_property_roundtrip.py  # Property-based tests
│   ├── models/                       # Data models
│   ├── storage/                      # Storage utilities
│   ├── simple_server.py             # Main FastAPI server
│   ├── signaling_server.py          # Socket.IO signaling server
│   ├── auth_service.py              # JWT authentication service
│   ├── meeting_service.py           # Meeting management API
│   ├── mock_inference.py            # Mock ASL inference engine
│   ├── redis_client.py              # Redis client wrapper
│   ├── cloud_storage.py             # Cloud storage integration
│   ├── requirements.txt             # Python dependencies
│   ├── Dockerfile                   # Backend Docker image
│   ├── .env.example                 # Backend environment template
│   ├── AUTH_SERVICE_README.md       # Auth service documentation
│   ├── SIGNALING_SERVER_README.md   # Signaling server docs
│   ├── REDIS_SETUP.md               # Redis configuration guide
│   ├── CLOUD_STORAGE_SETUP.md       # Cloud storage guide
│   └── MEETING_SERVICE_API.md       # Meeting API documentation
├── frontend/                         # React TypeScript frontend
│   ├── src/
│   │   ├── components/              # Reusable UI components
│   │   │   ├── VideoGrid.tsx        # Video grid layout
│   │   │   ├── VideoTile.tsx        # Individual video tile
│   │   │   ├── ControlBar.tsx       # Meeting controls
│   │   │   ├── ChatPanel.tsx        # Chat interface
│   │   │   └── ui/                  # UI primitives
│   │   ├── pages/                   # Page components
│   │   │   ├── LandingPageNew.tsx   # Landing page
│   │   │   ├── DashboardNew.tsx     # User dashboard
│   │   │   ├── PreJoinLobby.tsx     # Pre-meeting lobby
│   │   │   ├── MeetingRoom.tsx      # Main meeting room
│   │   │   └── VideoCallPage.tsx    # Video call interface
│   │   ├── contexts/                # React Context providers
│   │   │   ├── AppContext.tsx       # Global app state
│   │   │   ├── AuthContext.tsx      # Authentication state
│   │   │   ├── MeetingContext.tsx   # Meeting state
│   │   │   └── WebSocketContext.tsx # Socket.IO connection
│   │   ├── hooks/                   # Custom React hooks
│   │   │   └── useWebRTC.ts         # WebRTC hook
│   │   ├── services/                # API and service integrations
│   │   │   ├── api.ts               # Backend API client
│   │   │   └── FrameCaptureManager.ts  # Frame capture logic
│   │   ├── types/                   # TypeScript type definitions
│   │   ├── utils/                   # Utility functions
│   │   ├── App.tsx                  # Main app component
│   │   └── main.tsx                 # Entry point
│   ├── public/                      # Static assets
│   ├── package.json                 # Node dependencies
│   ├── tsconfig.json                # TypeScript configuration
│   ├── vite.config.ts               # Vite configuration
│   ├── tailwind.config.js           # Tailwind CSS config
│   ├── Dockerfile                   # Frontend Docker image
│   ├── .env.example                 # Frontend environment template
│   └── SETUP.md                     # Frontend setup guide
├── ml/                              # Machine learning code
│   ├── model.py                     # Model definitions
│   ├── train.py                     # Training scripts
│   ├── evaluate.py                  # Evaluation scripts
│   ├── preprocess.py                # Data preprocessing
│   └── dataset_loader.py            # Dataset utilities
├── scripts/                         # Deployment scripts
│   ├── deploy.sh                    # Unix deployment script
│   └── deploy.ps1                   # Windows deployment script
├── docs/                            # Documentation
│   ├── CI_CD_SETUP.md              # CI/CD pipeline guide
│   └── DEPLOYMENT.md                # Deployment guide
├── .github/
│   └── workflows/
│       └── ci-cd.yml                # GitHub Actions workflow
├── docker-compose.yml               # Docker Compose configuration
├── .env.example                     # Root environment template
├── Makefile                         # Development commands
├── DEVELOPMENT.md                   # Development setup guide
├── PROJECT_SETUP.md                 # Project setup documentation
├── nginx.conf                       # Nginx configuration
├── .pre-commit-config.yaml          # Pre-commit hooks
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

## 📦 Installation & Setup

### Prerequisites

- **Docker & Docker Compose** (v20.10+) - Recommended for easiest setup
- **Node.js** (v20+) - For frontend development
- **Python** (v3.11+) - For backend development
- **PostgreSQL** (v15+) - If not using Docker
- **Redis** (v7+) - If not using Docker
- **Git** - Version control

### Option 1: Docker Setup (Recommended)

This is the easiest way to get started with all services:

```bash
# 1. Clone the repository
git clone <repository-url>
cd sign-language-translator

# 2. Copy environment files
cp .env.example .env
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env

# 3. Edit environment files (optional for development)
# Update database credentials, API keys, etc.

# 4. Start all services
docker-compose up -d

# 5. Initialize database schema
docker-compose exec backend python database/init_db.py init

# 6. Check service health
docker-compose ps
docker-compose logs -f

# 7. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8001
# PostgreSQL: localhost:5432
# Redis: localhost:6379
```

### Option 2: Manual Setup

#### Step 1: Database Setup

**PostgreSQL:**
```bash
# Install PostgreSQL 15
# Create database and user
psql -U postgres
CREATE DATABASE meeting_db;
CREATE USER meeting_user WITH PASSWORD 'meeting_pass';
GRANT ALL PRIVILEGES ON DATABASE meeting_db TO meeting_user;
\q

# Initialize schema
cd backend
python database/init_db.py init
```

**Redis:**
```bash
# Install Redis 7
# Start Redis server
redis-server

# Or on Windows with WSL
wsl redis-server
```

#### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment file
cp .env.example .env
# Edit .env with your database credentials

# Run the backend server
python simple_server.py
# Server will start on http://0.0.0.0:8001
```

#### Step 3: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy and configure environment file
cp .env.example .env
# Edit .env with your backend URL

# Start the development server
npm run dev
# Frontend will start on http://localhost:5173
```

### Option 3: Using Makefile

The project includes a Makefile for common tasks:

```bash
# Initial setup (copy env files)
make setup

# Install all dependencies
make install

# Start all services with Docker
make start

# Stop all services
make stop

# View logs
make logs

# Run tests
make test

# Run linters
make lint

# Format code
make format

# Initialize database
make db-init

# Reset database (WARNING: deletes all data)
make db-reset

# Open PostgreSQL shell
make db-shell

# Open Redis shell
make redis-shell

# Clean up containers and volumes
make clean
```

### Verification

After setup, verify everything is working:

```bash
# Check backend health
curl http://localhost:8001/health

# Check Redis health
curl http://localhost:8001/health/redis

# Check database connection
docker-compose exec postgres psql -U meeting_user -d meeting_db -c "\dt"

# Check frontend
open http://localhost:5173
```

## ⚙️ Environment Configuration

### Backend Environment Variables

Create `backend/.env` from `backend/.env.example`:

```bash
# Database Configuration
DATABASE_URL=postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=50
REDIS_SESSION_TTL_SECONDS=3600
REDIS_FRAME_BUFFER_MAX_SIZE=60

# Server Configuration
PORT=8001
HOST=0.0.0.0
LOG_LEVEL=INFO
ENVIRONMENT=development

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Authentication & Security
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Feature Flags
FEATURE_USE_MOCK_MODEL=1
FEATURE_ENABLE_TTS=1
FEATURE_ENABLE_RECORDING=1
FEATURE_ENABLE_TRANSCRIPTION=1
FEATURE_ENABLE_AI_SUMMARY=1
FEATURE_ENABLE_SIGN_LANGUAGE=1

# Cloud Storage (choose: s3, gcs, or local)
STORAGE_PROVIDER=local
STORAGE_BUCKET_NAME=meeting-recordings
LOCAL_STORAGE_PATH=./storage

# AWS S3 (if using S3)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# Google Cloud Storage (if using GCS)
GCS_PROJECT_ID=
GCS_CREDENTIALS_PATH=

# WebRTC Configuration
STUN_SERVER_URL=stun:stun.l.google.com:19302
TURN_SERVER_URL=
TURN_SERVER_USERNAME=
TURN_SERVER_CREDENTIAL=

# ML Model Configuration
INFERENCE_DEVICE=cpu
INFERENCE_CONFIDENCE_THRESHOLD=0.7
SIGN_LANGUAGE_MODEL_VERSION=latest
```

### Frontend Environment Variables

Create `frontend/.env` from `frontend/.env.example`:

```bash
# Backend API Configuration
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001

# Feature Flags
VITE_ENABLE_MOCK_INFERENCE=true
VITE_ENABLE_TTS=true
VITE_ENABLE_RECORDING=false
VITE_ENABLE_TRANSCRIPTION=false
```

### Docker Compose Environment

Create `.env` in the root directory:

```bash
# PostgreSQL
POSTGRES_DB=meeting_db
POSTGRES_USER=meeting_user
POSTGRES_PASSWORD=meeting_pass

# Redis
REDIS_PASSWORD=

# Backend
BACKEND_PORT=8001

# Frontend
FRONTEND_PORT=5173
```

### Generating Secure Keys

```bash
# Generate JWT secret key
openssl rand -hex 32

# Generate random password
openssl rand -base64 32
```

## 🔧 Development Workflow

### Code Quality Tools

#### Pre-commit Hooks

Install pre-commit hooks to automatically format and lint code:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

#### Backend (Python)

**Formatting:**
```bash
cd backend

# Format with Black
black .

# Sort imports with isort
isort .

# Check formatting without changes
black --check .
isort --check-only .
```

**Linting:**
```bash
cd backend

# Lint with flake8
flake8 .

# Type checking with mypy (if configured)
mypy .
```

**Testing:**
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_auth_service.py -v

# Run specific test
pytest test_auth_service.py::test_create_access_token -v
```

#### Frontend (TypeScript/React)

**Formatting:**
```bash
cd frontend

# Format with Prettier
npm run format

# Check formatting without changes
npm run format:check
```

**Linting:**
```bash
cd frontend

# Lint with ESLint
npm run lint

# Fix linting issues automatically
npm run lint -- --fix

# Type checking
npx tsc --noEmit
```

**Testing:**
```bash
cd frontend

# Run tests once
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

### Development Commands

#### Using Makefile

```bash
# Start all services
make start

# Stop all services
make stop

# Restart services
make restart

# View logs
make logs

# Run all tests
make test

# Run linters
make lint

# Format code
make format

# Clean up
make clean
```

#### Using Docker Compose

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend

# Rebuild images
docker-compose build

# Rebuild and restart
docker-compose up -d --build

# Execute command in container
docker-compose exec backend python database/init_db.py check
```

#### Running Services Individually

**Backend:**
```bash
cd backend
python simple_server.py
# Or with auto-reload
uvicorn simple_server:app --reload --host 0.0.0.0 --port 8001
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Signaling Server:**
```bash
cd backend
python signaling_server.py
```

### Database Management

```bash
# Initialize database schema
make db-init
# Or manually:
python backend/database/init_db.py init

# Check existing tables
make db-check
# Or manually:
python backend/database/init_db.py check

# Reset database (WARNING: deletes all data)
make db-reset

# Open PostgreSQL shell
make db-shell
# Or manually:
docker-compose exec postgres psql -U meeting_user -d meeting_db

# Run database tests
pytest backend/database/test_schema.py -v
pytest backend/database/test_property_roundtrip.py -v
```

### Redis Management

```bash
# Open Redis CLI
make redis-shell
# Or manually:
docker-compose exec redis redis-cli

# Clear Redis cache
make redis-clear
# Or manually:
docker-compose exec redis redis-cli FLUSHALL

# Check Redis health
curl http://localhost:8001/health/redis

# Monitor Redis commands
docker-compose exec redis redis-cli MONITOR
```

### Hot Reloading

Both frontend and backend support hot reloading during development:

- **Frontend**: Vite automatically reloads on file changes
- **Backend**: Uvicorn with `--reload` flag reloads on Python file changes

### Debugging

**Backend:**
```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use debugpy for VS Code
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

**Frontend:**
```typescript
// Use browser DevTools
console.log('Debug info:', data);
debugger; // Breakpoint
```

**VS Code Launch Configuration:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["simple_server:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

## 🚀 CI/CD Pipeline

The project uses GitHub Actions for automated testing and deployment.

### Pipeline Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflow                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Backend   │  │  Frontend   │  │   Build &   │         │
│  │   Linting   │  │   Linting   │  │    Push     │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                 │                 │                 │
│  ┌──────▼──────┐  ┌──────▼──────┐         │                 │
│  │   Backend   │  │  Frontend   │         │                 │
│  │    Tests    │  │    Tests    │         │                 │
│  └──────┬──────┘  └──────┬──────┘         │                 │
│         │                 │                 │                 │
│         └─────────┬───────┘                 │                 │
│                   │                         │                 │
│                   └─────────────────────────┘                 │
│                             │                                 │
│                   ┌─────────▼─────────┐                      │
│                   │   Deploy Staging  │ (develop branch)     │
│                   │       or          │                      │
│                   │ Deploy Production │ (main branch)        │
│                   └───────────────────┘                      │
└──────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

#### 1. Linting & Type Checking

**Backend:**
- Black formatter check
- isort import sorting check
- flake8 linting

**Frontend:**
- ESLint
- Prettier check
- TypeScript type checking

#### 2. Testing

**Backend:**
- pytest with PostgreSQL and Redis services
- Unit tests for all services
- Integration tests
- Property-based tests

**Frontend:**
- Vitest with React Testing Library
- Component tests
- Hook tests
- Integration tests

#### 3. Docker Build & Push

- Builds Docker images for backend and frontend
- Pushes to GitHub Container Registry (ghcr.io)
- Tags: `latest` (main), `develop`, `<branch>-<sha>`

#### 4. Deployment

- **Staging**: Auto-deploy on push to `develop` branch
- **Production**: Auto-deploy on push to `main` branch

### Running CI Checks Locally

**Backend:**
```bash
cd backend

# Linting
black --check .
isort --check-only .
flake8 .

# Tests
pytest -v --cov=. --cov-report=html
```

**Frontend:**
```bash
cd frontend

# Linting
npm run lint
npm run format:check
npx tsc --noEmit

# Tests
npm run test
```

### Docker Images

Images are automatically built and pushed to GitHub Container Registry:

```bash
# Pull latest images
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO/backend:latest
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO/frontend:latest

# Run with Docker Compose
docker-compose pull
docker-compose up -d
```

### Required GitHub Secrets

Configure these in **Settings → Secrets and variables → Actions**:

**For GitHub Container Registry** (default):
- `GITHUB_TOKEN` - Automatically provided

**For External Docker Registry** (optional):
- `DOCKER_REGISTRY_URL`
- `DOCKER_REGISTRY_USERNAME`
- `DOCKER_REGISTRY_PASSWORD`

**For Staging Deployment**:
- `STAGING_HOST`
- `STAGING_SSH_KEY`
- `STAGING_DATABASE_URL`
- `STAGING_REDIS_URL`

**For Production Deployment**:
- `PRODUCTION_HOST`
- `PRODUCTION_SSH_KEY`
- `PRODUCTION_DATABASE_URL`
- `PRODUCTION_REDIS_URL`

### Status Badges

Add to your README:

```markdown
[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci-cd.yml)
```

### Health Check Endpoints

The backend provides health check endpoints for monitoring:

**Overall Health:**
```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "service": "backend",
  "active_rooms": 5,
  "active_connections": 12,
  "timestamp": "2024-01-15T10:30:00",
  "redis": {
    "status": "healthy",
    "ping": true,
    "info": "Redis 7.0.0"
  }
}
```

**Redis Health:**
```bash
curl http://localhost:8001/health/redis
```

For more details, see [docs/CI_CD_SETUP.md](docs/CI_CD_SETUP.md).

## 📚 API Documentation

### Authentication Service

**Base URL**: `http://localhost:8001/api/auth`

#### POST /api/auth/register
Register a new user account.

```bash
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "securepassword123"
  }'
```

#### POST /api/auth/login
Authenticate and receive JWT tokens.

```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### GET /api/auth/me
Get current user information (requires authentication).

```bash
curl http://localhost:8001/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### Meeting Service

**Base URL**: `http://localhost:8001/api/meetings`

#### POST /api/meetings
Create a new meeting.

```bash
curl -X POST http://localhost:8001/api/meetings \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Standup",
    "scheduled_start": "2024-01-15T10:00:00Z",
    "duration_minutes": 30,
    "settings": {
      "enable_recording": true,
      "enable_captions": true,
      "max_participants": 10
    }
  }'
```

#### GET /api/meetings/{meeting_id}
Get meeting details.

```bash
curl http://localhost:8001/api/meetings/meeting-123 \
  -H "Authorization: Bearer <access_token>"
```

#### GET /api/meetings/{meeting_id}/participants
Get meeting participants.

```bash
curl http://localhost:8001/api/meetings/meeting-123/participants \
  -H "Authorization: Bearer <access_token>"
```

#### POST /api/meetings/{meeting_id}/join
Join a meeting.

```bash
curl -X POST http://localhost:8001/api/meetings/meeting-123/join \
  -H "Authorization: Bearer <access_token>"
```

### WebSocket Events (Socket.IO)

**Connection URL**: `ws://localhost:8001/socket.io`

#### Client → Server Events

**join-meeting**
```javascript
socket.emit('join-meeting', {
  meetingId: 'meeting-123',
  userId: 'user-456',
  mediaCapabilities: {
    audio: true,
    video: true,
    screenShare: false
  }
});
```

**offer** (WebRTC)
```javascript
socket.emit('offer', {
  to: 'user-789',
  from: 'user-456',
  sdp: rtcPeerConnection.localDescription
});
```

**answer** (WebRTC)
```javascript
socket.emit('answer', {
  to: 'user-456',
  from: 'user-789',
  sdp: rtcPeerConnection.localDescription
});
```

**ice-candidate** (WebRTC)
```javascript
socket.emit('ice-candidate', {
  to: 'user-789',
  from: 'user-456',
  candidate: event.candidate
});
```

#### Server → Client Events

**participant-joined**
```javascript
socket.on('participant-joined', (data) => {
  console.log('New participant:', data.participant);
});
```

**participant-left**
```javascript
socket.on('participant-left', (data) => {
  console.log('Participant left:', data.userId);
});
```

**offer** (WebRTC)
```javascript
socket.on('offer', async (data) => {
  await rtcPeerConnection.setRemoteDescription(data.sdp);
  // Create and send answer
});
```

### Health Endpoints

#### GET /health
Overall service health.

```bash
curl http://localhost:8001/health
```

#### GET /health/redis
Redis health check.

```bash
curl http://localhost:8001/health/redis
```

### Rate Limiting

All authenticated endpoints are rate-limited to **100 requests per minute per user**.

Response headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

### Error Responses

**400 Bad Request**
```json
{
  "detail": "Invalid request data"
}
```

**401 Unauthorized**
```json
{
  "detail": "Could not validate credentials"
}
```

**404 Not Found**
```json
{
  "detail": "Meeting not found"
}
```

**429 Too Many Requests**
```json
{
  "detail": "Rate limit exceeded. Maximum 100 requests per minute."
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

For detailed API documentation, see:
- [backend/AUTH_SERVICE_README.md](backend/AUTH_SERVICE_README.md)
- [backend/MEETING_SERVICE_API.md](backend/MEETING_SERVICE_API.md)
- [backend/SIGNALING_SERVER_README.md](backend/SIGNALING_SERVER_README.md)

## 🧪 Testing

### Backend Testing

#### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_auth_service.py -v

# Run specific test
pytest test_auth_service.py::test_create_access_token -v

# Run tests matching pattern
pytest -k "auth" -v
```

#### Test Categories

**Unit Tests:**
- `test_auth_service.py` - Authentication service tests
- `test_meeting_service.py` - Meeting service tests
- `test_redis_client.py` - Redis client tests
- `test_cloud_storage.py` - Cloud storage tests
- `test_signaling_server.py` - Signaling server tests

**Database Tests:**
- `database/test_schema.py` - Schema validation tests
- `database/test_property_roundtrip.py` - Property-based tests

**Integration Tests:**
- `test_participant_endpoints.py` - Participant API tests

#### Property-Based Testing

The project uses property-based testing for database operations:

```bash
# Run property tests
pytest backend/database/test_property_roundtrip.py -v

# Run with more examples
pytest backend/database/test_property_roundtrip.py -v --hypothesis-show-statistics
```

### Frontend Testing

#### Running Tests

```bash
cd frontend

# Run tests once
npm test

# Run in watch mode
npm run test:watch

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- VideoGrid.test.tsx

# Run tests matching pattern
npm test -- --grep "camera"
```

#### Test Categories

**Component Tests:**
- `src/components/VideoGrid.test.tsx`
- `src/components/ControlBar.test.tsx`
- `src/components/ChatPanel.test.tsx`

**Hook Tests:**
- `src/hooks/useWebRTC.test.ts`

**Integration Tests:**
- `src/test/camera-preservation.test.tsx`
- `src/test/camera-bug-exploration.test.tsx`

#### Test Coverage

View coverage reports:

```bash
# Backend
cd backend
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend
npm run test:coverage
open coverage/index.html
```

### End-to-End Testing

For manual E2E testing:

1. Start all services
2. Open two browser tabs
3. Follow the testing checklist below

**Testing Checklist:**
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can create a room
- [ ] Can join a room with code
- [ ] Camera turns on/off reliably
- [ ] Both peers see each other's video
- [ ] Captions appear when accessibility mode is on
- [ ] Chat messages are exchanged
- [ ] TTS speaks captions
- [ ] Keyboard shortcuts work
- [ ] Can leave call cleanly

### Continuous Integration

Tests run automatically on:
- Pull requests
- Push to `develop` branch
- Push to `main` branch

View test results in GitHub Actions.

## 🌐 Deployment

### Deployment Options

1. **Docker Compose** - Simple single-server deployment
2. **Kubernetes** - Scalable container orchestration
3. **Cloud Platforms** - AWS, GCP, Azure
4. **Manual** - Traditional server deployment

### Docker Compose Deployment

**Production docker-compose.yml:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: always

  backend:
    image: ghcr.io/YOUR_USERNAME/YOUR_REPO/backend:latest
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
      - CORS_ORIGINS=https://yourdomain.com
      - LOG_LEVEL=INFO
    depends_on:
      - postgres
      - redis
    restart: always

  frontend:
    image: ghcr.io/YOUR_USERNAME/YOUR_REPO/frontend:latest
    environment:
      - VITE_API_URL=https://yourdomain.com/api
      - VITE_WS_URL=wss://yourdomain.com/ws
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: always

volumes:
  postgres_data:
  redis_data:
```

**Deploy:**

```bash
# Pull latest images
docker-compose pull

# Start services
docker-compose up -d

# Check health
curl https://yourdomain.com/health
```

### Nginx Configuration

Create `nginx.conf` for reverse proxy:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8001;
    }

    upstream frontend {
        server frontend:5173;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # WebSocket
        location /socket.io/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
```

### SSL/TLS Certificates

**Using Let's Encrypt:**

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Environment Variables for Production

**Critical changes for production:**

1. **Generate secure JWT secret:**
   ```bash
   openssl rand -hex 32
   ```

2. **Update CORS origins:**
   ```bash
   CORS_ORIGINS=https://yourdomain.com
   ```

3. **Use production database:**
   ```bash
   DATABASE_URL=postgresql://user:pass@prod-db:5432/meeting_db
   ```

4. **Configure cloud storage:**
   ```bash
   STORAGE_PROVIDER=s3
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   ```

5. **Disable debug features:**
   ```bash
   LOG_LEVEL=INFO
   FEATURE_USE_MOCK_MODEL=0
   DEBUG=0
   ```

### Deployment Scripts

**Unix/Linux:**
```bash
./scripts/deploy.sh
```

**Windows:**
```powershell
.\scripts\deploy.ps1
```

### Health Checks

Monitor service health:

```bash
# Overall health
curl https://yourdomain.com/health

# Redis health
curl https://yourdomain.com/health/redis

# Check all services
docker-compose ps
```

### Rollback Procedure

If deployment fails:

```bash
# Find previous image tag
docker images ghcr.io/YOUR_USERNAME/YOUR_REPO/backend

# Update docker-compose.yml to use previous tag
# backend:
#   image: ghcr.io/YOUR_USERNAME/YOUR_REPO/backend:previous-tag

# Restart services
docker-compose down
docker-compose up -d
```

### Monitoring

**Prometheus Metrics:**
```bash
curl https://yourdomain.com/metrics
```

**Log Aggregation:**
```bash
# View logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
```

### Backup Strategy

**Database Backup:**
```bash
# Backup
docker-compose exec postgres pg_dump -U meeting_user meeting_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U meeting_user meeting_db < backup.sql
```

**Redis Backup:**
```bash
# Backup
docker-compose exec redis redis-cli SAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./redis-backup.rdb

# Restore
docker cp ./redis-backup.rdb $(docker-compose ps -q redis):/data/dump.rdb
docker-compose restart redis
```

### Security Checklist

Before deploying to production:

- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall rules (allow only 80, 443)
- [ ] Set strong database passwords
- [ ] Enable Redis authentication
- [ ] Configure CORS to specific domains only
- [ ] Enable rate limiting
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Enable security headers in nginx
- [ ] Set up intrusion detection
- [ ] Configure automated security updates
- [ ] Use environment variables for secrets
- [ ] Disable debug mode
- [ ] Set up monitoring and alerting

For detailed deployment instructions, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## 🐛 Troubleshooting

### Common Issues

#### Backend Issues

**Port 8001 already in use:**

```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8001 | xargs kill -9

# Or change port in backend/.env
PORT=8002
```

**Python not found:**
- Install Python 3.11+ from https://www.python.org/downloads/
- Ensure "Add to PATH" is checked during installation
- Verify: `python --version`

**Module not found errors:**
```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

**Database connection failed:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify connection string in .env
DATABASE_URL=postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db

# Test connection
docker-compose exec postgres psql -U meeting_user -d meeting_db
```

**Redis connection failed:**
```bash
# Check if Redis is running
docker-compose ps redis

# Check logs
docker-compose logs redis

# Test connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Verify Redis URL in .env
REDIS_URL=redis://localhost:6379
```

#### Frontend Issues

**Port 5173 already in use:**

```bash
# Change port in frontend/vite.config.ts
server: { port: 3000 }

# Or kill process
# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5173 | xargs kill -9
```

**Node.js not found:**
- Install Node.js 20+ from https://nodejs.org/
- Verify: `node --version`

**npm ci fails:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Build errors:**
```bash
cd frontend

# Clear cache
rm -rf node_modules/.vite

# Reinstall dependencies
npm install

# Check TypeScript errors
npx tsc --noEmit
```

#### Camera Issues

**Camera not accessible:**
1. Close other apps using the camera (Zoom, Teams, etc.)
2. Check browser permissions:
   - Chrome: `chrome://settings/content/camera`
   - Firefox: `about:preferences#privacy`
3. Try a different browser (Chrome/Edge recommended)
4. Restart browser
5. Check if camera works in other apps

**Camera shows black screen:**
1. Refresh the page
2. Click "Turn On Camera" button again
3. Check browser console for errors (F12)
4. Try in incognito mode
5. Check camera permissions

**Camera permission denied:**
```javascript
// Check browser console for error
// DOMException: Permission denied

// Solutions:
// 1. Click the camera icon in address bar
// 2. Allow camera access
// 3. Refresh the page
```

#### WebRTC Connection Issues

**Peers can't see each other:**
1. Ensure both tabs are on the same room code
2. Check browser console for errors (F12)
3. Disable browser extensions (ad blockers)
4. Try in incognito mode
5. Check firewall settings
6. Verify STUN server is accessible

**No video/audio:**
1. Check camera/mic permissions
2. Ensure STUN server is accessible (requires internet)
3. Check firewall settings
4. Try different STUN server in .env:
   ```bash
   STUN_SERVER_URL=stun:stun.l.google.com:19302
   ```

**High latency:**
1. Check network connection
2. Use TURN server for NAT traversal
3. Reduce video quality
4. Check CPU usage

#### Docker Issues

**Docker daemon not running:**
```bash
# Windows/Mac: Start Docker Desktop
# Linux:
sudo systemctl start docker
```

**Permission denied:**
```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
```

**Out of disk space:**
```bash
# Clean up Docker
docker system prune -a --volumes

# Check disk usage
docker system df
```

**Container won't start:**
```bash
# Check logs
docker-compose logs <service-name>

# Restart service
docker-compose restart <service-name>

# Rebuild image
docker-compose build <service-name>
docker-compose up -d <service-name>
```

### Debug Mode

**Enable debug logging:**

Backend:
```bash
# In backend/.env
LOG_LEVEL=DEBUG
```

Frontend:
```javascript
// In browser console
localStorage.setItem('debug', '*');
// Refresh page
```

### Getting Help

1. Check this troubleshooting section
2. Review application logs:
   ```bash
   docker-compose logs -f
   ```
3. Check browser console (F12)
4. Review GitHub Issues
5. Check documentation:
   - [DEVELOPMENT.md](DEVELOPMENT.md)
   - [backend/AUTH_SERVICE_README.md](backend/AUTH_SERVICE_README.md)
   - [backend/SIGNALING_SERVER_README.md](backend/SIGNALING_SERVER_README.md)
   - [frontend/SETUP.md](frontend/SETUP.md)

### Performance Issues

**Slow application:**
1. Check system resources: `docker stats`
2. Check database query performance
3. Check Redis performance
4. Review Prometheus metrics
5. Enable caching
6. Optimize database queries

**High memory usage:**
```bash
# Check container memory
docker stats

# Increase memory limits in docker-compose.yml
services:
  backend:
    mem_limit: 2g
```

**High CPU usage:**
1. Check for infinite loops in code
2. Optimize inference processing
3. Reduce frame capture rate
4. Use production build (not dev mode)

## 🎮 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `M` | Toggle microphone |
| `V` | Toggle camera |
| `A` | Toggle accessibility mode |
| `P` | Pause/resume gesture detection |
| `S` | Toggle screen sharing |
| `C` | Open/close chat panel |
| `Ctrl+C` | Clear all captions |
| `Ctrl+S` | Speak captions aloud |
| `Enter` | Confirm current caption |
| `Esc` | Leave meeting |

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/sign-language-translator.git
   cd sign-language-translator
   ```
3. Create a branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. Set up development environment (see [Installation & Setup](#installation--setup))

### Code Style

**Backend (Python):**
- Follow PEP 8 style guide
- Use Black for formatting
- Use isort for import sorting
- Use type hints
- Write docstrings for functions and classes

**Frontend (TypeScript/React):**
- Follow Airbnb style guide
- Use Prettier for formatting
- Use ESLint for linting
- Write JSDoc comments for complex functions
- Use TypeScript types (avoid `any`)

### Commit Messages

Follow conventional commits:

```
feat: add screen sharing feature
fix: resolve camera permission issue
docs: update API documentation
test: add tests for auth service
refactor: simplify WebRTC connection logic
chore: update dependencies
```

### Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass:
   ```bash
   make test
   ```
4. Ensure code is formatted:
   ```bash
   make format
   make lint
   ```
5. Update CHANGELOG.md (if applicable)
6. Submit pull request with clear description
7. Link related issues

### Testing Requirements

- All new features must include tests
- Maintain or improve code coverage
- All tests must pass in CI/CD pipeline

### Code Review

- All PRs require at least one approval
- Address review comments
- Keep PRs focused and reasonably sized
- Rebase on main before merging

### Areas for Contribution

**High Priority:**
- [ ] Real ASL model training and integration
- [ ] Recording service implementation
- [ ] Transcription service integration
- [ ] AI summary generation
- [ ] Breakout rooms feature
- [ ] Screen sharing improvements

**Medium Priority:**
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Calendar integration (Google, Outlook)
- [ ] Email notifications
- [ ] User profile management
- [ ] Meeting analytics dashboard

**Low Priority:**
- [ ] Custom gesture recognition
- [ ] Virtual backgrounds
- [ ] Meeting templates
- [ ] Keyboard shortcut customization
- [ ] Dark mode improvements

### Reporting Bugs

Use GitHub Issues with the bug template:

1. Clear description of the issue
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Screenshots (if applicable)
6. Environment details (OS, browser, versions)
7. Error logs

### Feature Requests

Use GitHub Issues with the feature request template:

1. Clear description of the feature
2. Use case and motivation
3. Proposed solution
4. Alternative solutions considered
5. Additional context

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Sign Language Video Call Application

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 📖 Additional Documentation

### Core Documentation
- [DEVELOPMENT.md](DEVELOPMENT.md) - Detailed development setup guide
- [PROJECT_SETUP.md](PROJECT_SETUP.md) - Project setup documentation
- [docs/CI_CD_SETUP.md](docs/CI_CD_SETUP.md) - CI/CD pipeline configuration
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Production deployment guide

### Backend Documentation
- [backend/AUTH_SERVICE_README.md](backend/AUTH_SERVICE_README.md) - Authentication service
- [backend/SIGNALING_SERVER_README.md](backend/SIGNALING_SERVER_README.md) - WebRTC signaling
- [backend/MEETING_SERVICE_API.md](backend/MEETING_SERVICE_API.md) - Meeting API
- [backend/REDIS_SETUP.md](backend/REDIS_SETUP.md) - Redis configuration
- [backend/CLOUD_STORAGE_SETUP.md](backend/CLOUD_STORAGE_SETUP.md) - Cloud storage setup
- [backend/database/README.md](backend/database/README.md) - Database schema
- [backend/database/PROPERTY_TESTS_README.md](backend/database/PROPERTY_TESTS_README.md) - Property-based testing

### Frontend Documentation
- [frontend/SETUP.md](frontend/SETUP.md) - Frontend setup guide
- [frontend/src/components/ControlBar.README.md](frontend/src/components/ControlBar.README.md) - Control bar component
- [frontend/src/components/VideoGrid.README.md](frontend/src/components/VideoGrid.README.md) - Video grid component
- [frontend/src/hooks/useWebRTC.README.md](frontend/src/hooks/useWebRTC.README.md) - WebRTC hook
- [frontend/src/pages/MeetingRoom.README.md](frontend/src/pages/MeetingRoom.README.md) - Meeting room page

### Specification Documents
- [.kiro/specs/advanced-meeting-features/requirements.md](.kiro/specs/advanced-meeting-features/requirements.md) - Feature requirements
- [.kiro/specs/advanced-meeting-features/design.md](.kiro/specs/advanced-meeting-features/design.md) - Technical design
- [.kiro/specs/advanced-meeting-features/tasks.md](.kiro/specs/advanced-meeting-features/tasks.md) - Implementation tasks

## 🎯 Demo Script (2 Minutes)

**For presentations and demos:**

1. **Introduction** (15 seconds)
   - "I'll show you a video call app with real-time sign language recognition."

2. **Setup** (30 seconds)
   - Open two browser tabs
   - Tab 1 creates a room, Tab 2 joins with the code
   - Enable cameras in both tabs

3. **Video Call** (30 seconds)
   - "Both participants can see each other in real-time."
   - Show video quality and responsiveness

4. **ASL Recognition** (45 seconds)
   - Turn on Accessibility Mode in Tab 1
   - "Now I enable ASL recognition."
   - Wave hand in front of camera
   - "The system detects hand gestures and generates captions in real-time."
   - "Tab 2 sees the captions appear automatically."

5. **Text-to-Speech** (15 seconds)
   - Click speaker icon
   - "The browser reads the captions aloud using text-to-speech."

6. **Chat** (15 seconds)
   - Type in chat
   - "We also have text chat for additional communication."

7. **Conclusion** (15 seconds)
   - "This enables deaf/hard-of-hearing users to communicate naturally in video calls."

**Total time: ~2 minutes**

## 🚀 Roadmap

### Phase 1: Core Features (Completed)
- ✅ WebRTC video calling
- ✅ Mock ASL recognition
- ✅ Live captions
- ✅ Text-to-speech
- ✅ Chat system
- ✅ Meeting management
- ✅ Authentication
- ✅ Database integration
- ✅ Redis caching

### Phase 2: Advanced Features (In Progress)
- 🔄 Real ASL model training
- 🔄 Recording service
- 🔄 Transcription service
- 🔄 AI summaries
- 🔄 Screen sharing
- 🔄 Breakout rooms
- 🔄 Waiting room

### Phase 3: Production Ready (Planned)
- ⏳ TURN server integration
- ⏳ End-to-end encryption
- ⏳ Mobile app (React Native)
- ⏳ Multi-language support
- ⏳ Calendar integration
- ⏳ Email notifications
- ⏳ Analytics dashboard

### Phase 4: Scale & Optimize (Future)
- ⏳ Kubernetes deployment
- ⏳ Load balancing
- ⏳ CDN integration
- ⏳ Performance optimization
- ⏳ Advanced monitoring
- ⏳ A/B testing framework

## 🙏 Acknowledgments

- **MediaPipe** - Hand landmark detection
- **WebRTC** - Real-time communication
- **FastAPI** - Modern Python web framework
- **React** - UI framework
- **Socket.IO** - Real-time bidirectional communication
- **PostgreSQL** - Reliable database
- **Redis** - Fast caching and session storage

## 📞 Support

For issues, questions, or contributions:

- **GitHub Issues**: [Report bugs or request features](https://github.com/YOUR_USERNAME/YOUR_REPO/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/YOUR_USERNAME/YOUR_REPO/discussions)
- **Documentation**: Check the [docs](docs/) directory
- **Email**: support@example.com (if applicable)

## 🌟 Star History

If you find this project useful, please consider giving it a star ⭐

---

**Built with ❤️ for accessibility**

**Making video calls accessible for everyone**

