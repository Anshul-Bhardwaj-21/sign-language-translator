# Deployment Guide

This guide covers deploying the Sign Language Video Call application to staging and production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [CI/CD Pipeline](#cicd-pipeline)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [Environment Variables](#environment-variables)
- [Health Checks](#health-checks)
- [Rollback Procedures](#rollback-procedures)
- [Monitoring](#monitoring)

## Prerequisites

### Required Tools

- Docker and Docker Compose
- kubectl (for Kubernetes deployments)
- GitHub account with repository access
- Cloud provider account (AWS, GCP, or Azure)

### Required Secrets

Configure these secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

1. **Container Registry** (if not using GitHub Container Registry):
   - `DOCKER_REGISTRY_URL`
   - `DOCKER_REGISTRY_USERNAME`
   - `DOCKER_REGISTRY_PASSWORD`

2. **Staging Environment**:
   - `STAGING_HOST` - Staging server hostname/IP
   - `STAGING_SSH_KEY` - SSH private key for deployment
   - `STAGING_DATABASE_URL` - PostgreSQL connection string
   - `STAGING_REDIS_URL` - Redis connection string

3. **Production Environment**:
   - `PRODUCTION_HOST` - Production server hostname/IP
   - `PRODUCTION_SSH_KEY` - SSH private key for deployment
   - `PRODUCTION_DATABASE_URL` - PostgreSQL connection string
   - `PRODUCTION_REDIS_URL` - Redis connection string

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) automatically:

1. **On Pull Request**: Runs linting and tests
2. **On Push to `develop`**: Builds images and deploys to staging
3. **On Push to `main`**: Builds images and deploys to production

### Pipeline Stages

```
┌─────────────┐
│   Linting   │ → Backend (Black, isort, flake8)
│             │ → Frontend (ESLint, Prettier, TypeScript)
└─────────────┘
       ↓
┌─────────────┐
│   Testing   │ → Backend (pytest with PostgreSQL/Redis)
│             │ → Frontend (Vitest)
└─────────────┘
       ↓
┌─────────────┐
│   Build     │ → Docker images (backend, frontend)
│   & Push    │ → Push to GitHub Container Registry
└─────────────┘
       ↓
┌─────────────┐
│   Deploy    │ → Staging (develop branch)
│             │ → Production (main branch)
└─────────────┘
```

## Staging Deployment

### Automatic Deployment

Staging deploys automatically when code is pushed to the `develop` branch:

```bash
git checkout develop
git merge feature/my-feature
git push origin develop
```

### Manual Deployment

To manually deploy to staging:

```bash
# SSH into staging server
ssh user@staging.example.com

# Pull latest images
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO/backend:develop
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO/frontend:develop

# Update docker-compose.yml to use new images
# Then restart services
docker-compose down
docker-compose up -d

# Check health
curl https://staging.example.com/health
```

### Staging Environment Configuration

Create a `docker-compose.staging.yml` file:

```yaml
version: '3.8'

services:
  backend:
    image: ghcr.io/YOUR_USERNAME/YOUR_REPO/backend:develop
    environment:
      - DATABASE_URL=${STAGING_DATABASE_URL}
      - REDIS_URL=${STAGING_REDIS_URL}
      - CORS_ORIGINS=https://staging.example.com
      - LOG_LEVEL=DEBUG
    restart: unless-stopped

  frontend:
    image: ghcr.io/YOUR_USERNAME/YOUR_REPO/frontend:develop
    environment:
      - VITE_API_URL=https://staging.example.com/api
      - VITE_WS_URL=wss://staging.example.com/ws
    restart: unless-stopped

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
    restart: unless-stopped
```

## Production Deployment

### Automatic Deployment

Production deploys automatically when code is pushed to the `main` branch:

```bash
git checkout main
git merge develop
git push origin main
```

### Manual Deployment

For critical updates or rollbacks:

```bash
# SSH into production server
ssh user@production.example.com

# Pull specific version
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO/backend:v1.2.3
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO/frontend:v1.2.3

# Update and restart
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d

# Verify health
curl https://example.com/health
```

### Production Environment Configuration

Create a `docker-compose.production.yml` file:

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
      - CORS_ORIGINS=https://example.com
      - LOG_LEVEL=INFO
      - FEATURE_USE_MOCK_MODEL=0
    depends_on:
      - postgres
      - redis
    restart: always

  frontend:
    image: ghcr.io/YOUR_USERNAME/YOUR_REPO/frontend:latest
    environment:
      - VITE_API_URL=https://example.com/api
      - VITE_WS_URL=wss://example.com/ws
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

## Environment Variables

### Backend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `REDIS_URL` | Redis connection string | Yes | - |
| `PORT` | Server port | No | 8001 |
| `HOST` | Server host | No | 0.0.0.0 |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | Yes | - |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |
| `FEATURE_USE_MOCK_MODEL` | Use mock inference (1) or real model (0) | No | 1 |
| `FEATURE_ENABLE_TTS` | Enable text-to-speech | No | 1 |

### Frontend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `VITE_API_URL` | Backend API URL | Yes | - |
| `VITE_WS_URL` | WebSocket URL | Yes | - |

## Health Checks

### Backend Health Endpoints

1. **Overall Health**: `GET /health`
   ```bash
   curl https://example.com/health
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

2. **Redis Health**: `GET /health/redis`
   ```bash
   curl https://example.com/health/redis
   ```

### Monitoring Health Checks

Add health check monitoring to your deployment:

```yaml
# docker-compose.yml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Rollback Procedures

### Quick Rollback

If a deployment causes issues, rollback to the previous version:

```bash
# Find previous image tag
docker images ghcr.io/YOUR_USERNAME/YOUR_REPO/backend

# Update docker-compose to use previous tag
# Then restart
docker-compose down
docker-compose up -d
```

### Automated Rollback

The CI/CD pipeline can be configured to automatically rollback on health check failures:

```yaml
# .github/workflows/ci-cd.yml
- name: Health check
  run: |
    for i in {1..5}; do
      if curl -f https://example.com/health; then
        echo "Health check passed"
        exit 0
      fi
      echo "Health check failed, retrying..."
      sleep 10
    done
    echo "Health check failed after 5 attempts, rolling back..."
    # Rollback commands here
    exit 1
```

## Monitoring

### Prometheus Metrics

The backend exposes Prometheus metrics at `/metrics`:

```bash
curl https://example.com/metrics
```

Key metrics:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `active_rooms` - Number of active rooms
- `active_connections` - Number of active WebSocket connections
- `inference_latency_seconds` - Sign language inference latency

### Grafana Dashboard

Import the provided Grafana dashboard (`monitoring/grafana-dashboard.json`) to visualize:

- Request rate and latency
- Active rooms and connections
- Error rates
- System resources (CPU, memory)
- Redis performance

### Log Aggregation

Configure log shipping to your preferred service:

```yaml
# docker-compose.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Or use a log aggregation service like:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Grafana Loki
- CloudWatch Logs (AWS)
- Cloud Logging (GCP)

## Troubleshooting

### Deployment Fails

1. Check GitHub Actions logs
2. Verify all secrets are configured
3. Check server disk space: `df -h`
4. Check Docker logs: `docker-compose logs`

### Health Checks Fail

1. Check service logs: `docker-compose logs backend`
2. Verify database connectivity: `docker-compose exec backend python -c "import psycopg2; print('OK')"`
3. Verify Redis connectivity: `docker-compose exec redis redis-cli ping`

### High Latency

1. Check system resources: `docker stats`
2. Review Prometheus metrics
3. Check database query performance
4. Verify network connectivity

## Security Checklist

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

## Support

For deployment issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review GitHub Actions logs
3. Check application logs: `docker-compose logs`
4. Open an issue on GitHub

---

**Last Updated**: 2024-01-15
