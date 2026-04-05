# CI/CD Setup Guide

This guide explains how to set up and configure the CI/CD pipeline for the Sign Language Video Call application.

## Overview

The CI/CD pipeline uses GitHub Actions to automatically:
- Run linting and type checking
- Execute tests
- Build Docker images
- Deploy to staging and production environments

## Pipeline Architecture

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
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Enable GitHub Actions

1. Go to your GitHub repository
2. Click on "Actions" tab
3. If prompted, click "I understand my workflows, go ahead and enable them"

### 2. Configure Secrets

Navigate to: **Settings → Secrets and variables → Actions → New repository secret**

#### Required Secrets

**For GitHub Container Registry (default)**:
- No additional secrets needed - uses `GITHUB_TOKEN` automatically

**For External Docker Registry** (optional):
```
DOCKER_REGISTRY_URL=docker.io
DOCKER_REGISTRY_USERNAME=your_username
DOCKER_REGISTRY_PASSWORD=your_password
```

**For Staging Deployment**:
```
STAGING_HOST=staging.example.com
STAGING_SSH_KEY=<your-ssh-private-key>
STAGING_DATABASE_URL=postgresql://user:pass@host:5432/db
STAGING_REDIS_URL=redis://host:6379
```

**For Production Deployment**:
```
PRODUCTION_HOST=example.com
PRODUCTION_SSH_KEY=<your-ssh-private-key>
PRODUCTION_DATABASE_URL=postgresql://user:pass@host:5432/db
PRODUCTION_REDIS_URL=redis://host:6379
```

### 3. Update Workflow File

Edit `.github/workflows/ci-cd.yml` and replace placeholders:

```yaml
env:
  REGISTRY: ghcr.io
  BACKEND_IMAGE_NAME: YOUR_USERNAME/YOUR_REPO/backend  # Update this
  FRONTEND_IMAGE_NAME: YOUR_USERNAME/YOUR_REPO/frontend  # Update this
```

### 4. Configure Branch Protection

Protect your main branches to ensure CI passes before merging:

1. Go to **Settings → Branches → Add branch protection rule**
2. Branch name pattern: `main`
3. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
4. Select required status checks:
   - Backend Linting
   - Backend Tests
   - Frontend Linting
   - Frontend Tests

Repeat for `develop` branch.

## Workflow Jobs

### 1. Backend Linting (`backend-lint`)

**Runs on**: All pushes and pull requests

**Steps**:
1. Checkout code
2. Set up Python 3.11
3. Install dependencies
4. Run Black formatter check
5. Run isort import sorting check
6. Run flake8 linting

**Local execution**:
```bash
cd backend
black --check .
isort --check-only .
flake8 .
```

### 2. Backend Tests (`backend-test`)

**Runs on**: All pushes and pull requests

**Services**:
- PostgreSQL 15 (test database)
- Redis 7 (test cache)

**Steps**:
1. Checkout code
2. Set up Python 3.11
3. Install dependencies
4. Run pytest with coverage

**Local execution**:
```bash
cd backend
pytest -v --cov=. --cov-report=html
```

### 3. Frontend Linting (`frontend-lint`)

**Runs on**: All pushes and pull requests

**Steps**:
1. Checkout code
2. Set up Node.js 20
3. Install dependencies
4. Run ESLint
5. Run Prettier check
6. Run TypeScript type checking

**Local execution**:
```bash
cd frontend
npm run lint
npm run format:check
npx tsc --noEmit
```

### 4. Frontend Tests (`frontend-test`)

**Runs on**: All pushes and pull requests

**Steps**:
1. Checkout code
2. Set up Node.js 20
3. Install dependencies
4. Run Vitest tests

**Local execution**:
```bash
cd frontend
npm run test
```

### 5. Build and Push (`build-and-push`)

**Runs on**: Push to `main` or `develop` branches (after all tests pass)

**Steps**:
1. Checkout code
2. Set up Docker Buildx
3. Log in to GitHub Container Registry
4. Build and push backend image
5. Build and push frontend image

**Image tags**:
- `latest` - Latest from main branch
- `develop` - Latest from develop branch
- `<branch>-<sha>` - Specific commit

**Local execution**:
```bash
# Backend
docker build -t backend:local ./backend
docker push ghcr.io/YOUR_USERNAME/YOUR_REPO/backend:local

# Frontend
docker build -t frontend:local ./frontend
docker push ghcr.io/YOUR_USERNAME/YOUR_REPO/frontend:local
```

### 6. Deploy Staging (`deploy-staging`)

**Runs on**: Push to `develop` branch (after build succeeds)

**Environment**: staging

**Steps**:
1. Checkout code
2. Deploy to staging server
3. Run health checks

**Deployment script** (customize in workflow):
```bash
# SSH into staging server
ssh -i $STAGING_SSH_KEY user@$STAGING_HOST << 'EOF'
  cd /opt/app
  docker-compose pull
  docker-compose up -d
  docker-compose ps
EOF

# Health check
curl -f https://staging.example.com/health || exit 1
```

### 7. Deploy Production (`deploy-production`)

**Runs on**: Push to `main` branch (after build succeeds)

**Environment**: production

**Steps**:
1. Checkout code
2. Deploy to production server
3. Run health checks

**Deployment script** (customize in workflow):
```bash
# SSH into production server
ssh -i $PRODUCTION_SSH_KEY user@$PRODUCTION_HOST << 'EOF'
  cd /opt/app
  docker-compose pull
  docker-compose up -d
  docker-compose ps
EOF

# Health check
curl -f https://example.com/health || exit 1
```

## Customizing Deployment

### Option 1: SSH Deployment (Simple)

Update the deploy steps in `.github/workflows/ci-cd.yml`:

```yaml
- name: Deploy to staging
  env:
    SSH_KEY: ${{ secrets.STAGING_SSH_KEY }}
    HOST: ${{ secrets.STAGING_HOST }}
  run: |
    echo "$SSH_KEY" > deploy_key
    chmod 600 deploy_key
    ssh -i deploy_key -o StrictHostKeyChecking=no user@$HOST << 'EOF'
      cd /opt/app
      docker-compose pull
      docker-compose up -d --remove-orphans
      docker-compose ps
    EOF
    rm deploy_key
```

### Option 2: Kubernetes Deployment

```yaml
- name: Deploy to staging
  run: |
    kubectl config use-context staging
    kubectl set image deployment/backend backend=${{ env.REGISTRY }}/${{ env.BACKEND_IMAGE_NAME }}:develop
    kubectl set image deployment/frontend frontend=${{ env.REGISTRY }}/${{ env.FRONTEND_IMAGE_NAME }}:develop
    kubectl rollout status deployment/backend
    kubectl rollout status deployment/frontend
```

### Option 3: Cloud Provider CLI

**AWS ECS**:
```yaml
- name: Deploy to staging
  run: |
    aws ecs update-service \
      --cluster staging-cluster \
      --service backend-service \
      --force-new-deployment
```

**Google Cloud Run**:
```yaml
- name: Deploy to staging
  run: |
    gcloud run deploy backend \
      --image ${{ env.REGISTRY }}/${{ env.BACKEND_IMAGE_NAME }}:develop \
      --platform managed \
      --region us-central1
```

## Monitoring Pipeline

### View Workflow Runs

1. Go to **Actions** tab in GitHub
2. Click on a workflow run to see details
3. Click on a job to see logs

### Status Badges

Add to your README.md:

```markdown
[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci-cd.yml)
```

### Notifications

Configure notifications in **Settings → Notifications**:
- Email notifications for failed workflows
- Slack integration (via GitHub app)
- Discord webhooks

## Troubleshooting

### Tests Fail in CI but Pass Locally

**Possible causes**:
1. Different Python/Node versions
2. Missing environment variables
3. Database/Redis not available

**Solutions**:
```bash
# Match CI Python version
pyenv install 3.11
pyenv local 3.11

# Match CI Node version
nvm install 20
nvm use 20

# Run with CI environment
export DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/test_db
export REDIS_URL=redis://localhost:6379
pytest
```

### Docker Build Fails

**Check**:
1. Dockerfile syntax
2. Build context size (should be < 1GB)
3. Network connectivity for package downloads

**Debug locally**:
```bash
docker build --progress=plain --no-cache ./backend
```

### Deployment Fails

**Check**:
1. SSH key is correct and has proper permissions
2. Server has enough disk space: `df -h`
3. Docker daemon is running: `systemctl status docker`
4. Images are accessible: `docker pull <image>`

**Debug**:
```bash
# Test SSH connection
ssh -i deploy_key user@host "echo 'Connection successful'"

# Check server logs
ssh -i deploy_key user@host "docker-compose logs --tail=100"
```

### Health Check Fails

**Check**:
1. Service is running: `docker-compose ps`
2. Port is accessible: `curl http://localhost:8001/health`
3. Database/Redis are healthy

**Debug**:
```bash
# Check service logs
docker-compose logs backend

# Test health endpoint
curl -v http://localhost:8001/health
```

## Best Practices

### 1. Use Caching

The workflow already uses caching for:
- Python pip packages
- Node.js npm packages
- Docker build layers

### 2. Fail Fast

Tests run in parallel to fail quickly if there are issues.

### 3. Separate Environments

Use different branches for different environments:
- `develop` → Staging
- `main` → Production
- Feature branches → No deployment

### 4. Manual Approval for Production

Add manual approval for production deployments:

```yaml
deploy-production:
  environment:
    name: production
    url: https://example.com
  # GitHub will require manual approval before running this job
```

### 5. Rollback Strategy

Keep previous images tagged:
```bash
# Tag before deploying
docker tag backend:latest backend:previous
docker tag backend:new backend:latest

# Rollback if needed
docker tag backend:previous backend:latest
docker-compose up -d
```

## Security Considerations

### 1. Secrets Management

- Never commit secrets to repository
- Use GitHub Secrets for sensitive data
- Rotate secrets regularly

### 2. Image Scanning

Add vulnerability scanning:

```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.REGISTRY }}/${{ env.BACKEND_IMAGE_NAME }}:latest
    format: 'sarif'
    output: 'trivy-results.sarif'
```

### 3. Dependency Updates

Use Dependabot to keep dependencies updated:

Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
  
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
```

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

---

**Last Updated**: 2024-01-15
