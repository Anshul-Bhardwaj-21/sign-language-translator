#!/bin/bash

# Quick Start Script for Advanced Meeting Features
# This script sets up the development environment and starts all services

set -e

echo "=========================================="
echo "Advanced Meeting Features - Quick Start"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Copy environment files if they don't exist
echo "Setting up environment files..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file"
fi

if [ ! -f frontend/.env ]; then
    cp frontend/.env.example frontend/.env
    echo "Created frontend/.env file"
fi

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "Created backend/.env file"
fi

echo ""
echo "Starting services with Docker Compose..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 5

echo ""
echo "=========================================="
echo "Services are starting!"
echo "=========================================="
echo ""
echo "Frontend:  http://localhost:5173"
echo "Backend:   http://localhost:8001"
echo "PostgreSQL: localhost:5432"
echo "Redis:     localhost:6379"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop:      docker-compose down"
echo ""
echo "For more commands, see DEVELOPMENT.md"
echo "=========================================="
