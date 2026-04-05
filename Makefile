.PHONY: help setup start stop restart logs clean test lint format

help:
	@echo "Available commands:"
	@echo "  make setup      - Initial setup (copy env files, install dependencies)"
	@echo "  make start      - Start all services with Docker Compose"
	@echo "  make stop       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View logs from all services"
	@echo "  make clean      - Clean up containers, volumes, and caches"
	@echo "  make test       - Run all tests"
	@echo "  make lint       - Run linters on backend and frontend"
	@echo "  make format     - Format code (backend and frontend)"
	@echo "  make install    - Install dependencies (backend and frontend)"
	@echo ""
	@echo "Database commands:"
	@echo "  make db-init    - Initialize database schema"
	@echo "  make db-check   - Check existing database tables"
	@echo "  make db-test    - Test database schema validity"
	@echo "  make db-reset   - Reset database (WARNING: deletes all data)"
	@echo "  make db-shell   - Open PostgreSQL shell"

setup:
	@echo "Setting up development environment..."
	@cp -n .env.example .env || true
	@cp -n frontend/.env.example frontend/.env || true
	@cp -n backend/.env.example backend/.env || true
	@echo "Environment files created. Please edit them with your configuration."
	@echo "Run 'make install' to install dependencies."

install:
	@echo "Installing backend dependencies..."
	@cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "Installing pre-commit hooks..."
	@pip install pre-commit
	@pre-commit install
	@echo "Dependencies installed!"

start:
	@echo "Starting all services..."
	@docker-compose up -d
	@echo "Services started! Frontend: http://localhost:5173, Backend: http://localhost:8001"

stop:
	@echo "Stopping all services..."
	@docker-compose down

restart:
	@echo "Restarting all services..."
	@docker-compose restart

logs:
	@docker-compose logs -f

clean:
	@echo "Cleaning up..."
	@docker-compose down -v
	@rm -rf backend/__pycache__ backend/**/__pycache__
	@rm -rf frontend/node_modules frontend/dist
	@rm -rf .pytest_cache
	@echo "Cleanup complete!"

test:
	@echo "Running backend tests..."
	@cd backend && pytest
	@echo "Running frontend tests..."
	@cd frontend && npm test

lint:
	@echo "Linting backend..."
	@cd backend && flake8 .
	@echo "Linting frontend..."
	@cd frontend && npm run lint

format:
	@echo "Formatting backend code..."
	@cd backend && black . && isort .
	@echo "Formatting frontend code..."
	@cd frontend && npm run format
	@echo "Code formatted!"

# Development without Docker
dev-backend:
	@echo "Starting backend in development mode..."
	@cd backend && uvicorn simple_server:app --host 0.0.0.0 --port 8001 --reload

dev-frontend:
	@echo "Starting frontend in development mode..."
	@cd frontend && npm run dev

# Database commands
db-init:
	@echo "Initializing database schema..."
	@python backend/database/init_db.py init
	@echo "Database initialized!"

db-check:
	@echo "Checking database tables..."
	@python backend/database/init_db.py check

db-test:
	@echo "Testing database schema..."
	@python backend/database/test_schema.py

db-reset:
	@echo "Resetting database..."
	@docker-compose down postgres
	@docker volume rm sign-language-translator-fixes_postgres_data || true
	@docker-compose up -d postgres
	@sleep 5
	@echo "Database reset complete! Schema will be initialized automatically."

db-shell:
	@docker-compose exec postgres psql -U meeting_user -d meeting_db

redis-shell:
	@docker-compose exec redis redis-cli

redis-clear:
	@docker-compose exec redis redis-cli FLUSHALL
	@echo "Redis cache cleared!"
