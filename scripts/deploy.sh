#!/bin/bash

# Deployment script for Sign Language Video Call Application
# Usage: ./deploy.sh [staging|production]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_info "Requirements check passed"
}

load_environment() {
    log_info "Loading environment: $ENVIRONMENT"
    
    if [ "$ENVIRONMENT" = "staging" ]; then
        export COMPOSE_FILE="docker-compose.staging.yml"
        export IMAGE_TAG="develop"
    elif [ "$ENVIRONMENT" = "production" ]; then
        export COMPOSE_FILE="docker-compose.production.yml"
        export IMAGE_TAG="latest"
    else
        log_error "Invalid environment: $ENVIRONMENT (use 'staging' or 'production')"
        exit 1
    fi
    
    log_info "Using compose file: $COMPOSE_FILE"
    log_info "Using image tag: $IMAGE_TAG"
}

pull_images() {
    log_info "Pulling latest Docker images..."
    
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" pull
    
    log_info "Images pulled successfully"
}

backup_database() {
    log_info "Creating database backup..."
    
    BACKUP_DIR="$PROJECT_ROOT/backups"
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/db_backup_${ENVIRONMENT}_${TIMESTAMP}.sql"
    
    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U meeting_user meeting_db > "$BACKUP_FILE" 2>/dev/null || {
        log_warn "Database backup failed (database might not be running yet)"
    }
    
    if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
        log_info "Database backed up to: $BACKUP_FILE"
    else
        log_warn "No database backup created"
        rm -f "$BACKUP_FILE"
    fi
}

deploy() {
    log_info "Deploying to $ENVIRONMENT..."
    
    cd "$PROJECT_ROOT"
    
    # Stop old containers
    log_info "Stopping old containers..."
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans
    
    # Start new containers
    log_info "Starting new containers..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_info "Deployment complete"
}

health_check() {
    log_info "Running health checks..."
    
    # Wait for services to start
    sleep 10
    
    # Check backend health
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:8001/health &> /dev/null; then
            log_info "Backend health check passed"
            return 0
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        log_warn "Health check attempt $RETRY_COUNT/$MAX_RETRIES failed, retrying..."
        sleep 2
    done
    
    log_error "Health check failed after $MAX_RETRIES attempts"
    return 1
}

show_status() {
    log_info "Service status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    log_info "\nRecent logs:"
    docker-compose -f "$COMPOSE_FILE" logs --tail=20
}

rollback() {
    log_error "Deployment failed, rolling back..."
    
    # Stop failed deployment
    docker-compose -f "$COMPOSE_FILE" down
    
    # Restore from backup if available
    LATEST_BACKUP=$(ls -t "$PROJECT_ROOT/backups/db_backup_${ENVIRONMENT}_"*.sql 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        log_info "Restoring database from: $LATEST_BACKUP"
        docker-compose -f "$COMPOSE_FILE" up -d postgres
        sleep 5
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U meeting_user meeting_db < "$LATEST_BACKUP"
    fi
    
    log_error "Rollback complete. Please investigate the issue."
    exit 1
}

# Main deployment flow
main() {
    log_info "Starting deployment to $ENVIRONMENT..."
    
    check_requirements
    load_environment
    pull_images
    backup_database
    deploy
    
    if health_check; then
        show_status
        log_info "Deployment to $ENVIRONMENT completed successfully!"
    else
        rollback
    fi
}

# Run main function
main
