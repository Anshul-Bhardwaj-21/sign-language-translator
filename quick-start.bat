@echo off
REM Quick Start Script for Advanced Meeting Features (Windows)
REM This script sets up the development environment and starts all services

echo ==========================================
echo Advanced Meeting Features - Quick Start
echo ==========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Copy environment files if they don't exist
echo Setting up environment files...
if not exist .env (
    copy .env.example .env
    echo Created .env file
)

if not exist frontend\.env (
    copy frontend\.env.example frontend\.env
    echo Created frontend\.env file
)

if not exist backend\.env (
    copy backend\.env.example backend\.env
    echo Created backend\.env file
)

echo.
echo Starting services with Docker Compose...
docker-compose up -d

echo.
echo Waiting for services to be ready...
timeout /t 5 /nobreak >nul

echo.
echo ==========================================
echo Services are starting!
echo ==========================================
echo.
echo Frontend:  http://localhost:5173
echo Backend:   http://localhost:8001
echo PostgreSQL: localhost:5432
echo Redis:     localhost:6379
echo.
echo To view logs: docker-compose logs -f
echo To stop:      docker-compose down
echo.
echo For more commands, see DEVELOPMENT.md
echo ==========================================
echo.
pause
