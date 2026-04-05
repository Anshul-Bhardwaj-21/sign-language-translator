# Deployment script for Sign Language Video Call Application
# Usage: .\deploy.ps1 [staging|production]

param(
    [Parameter(Position=0)]
    [ValidateSet("staging", "production")]
    [string]$Environment = "staging"
)

$ErrorActionPreference = "Stop"

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Check-Requirements {
    Write-Info "Checking requirements..."
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "Docker is not installed"
        exit 1
    }
    
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "Docker Compose is not installed"
        exit 1
    }
    
    Write-Info "Requirements check passed"
}

function Load-Environment {
    Write-Info "Loading environment: $Environment"
    
    if ($Environment -eq "staging") {
        $env:COMPOSE_FILE = "docker-compose.staging.yml"
        $env:IMAGE_TAG = "develop"
    }
    elseif ($Environment -eq "production") {
        $env:COMPOSE_FILE = "docker-compose.production.yml"
        $env:IMAGE_TAG = "latest"
    }
    
    Write-Info "Using compose file: $($env:COMPOSE_FILE)"
    Write-Info "Using image tag: $($env:IMAGE_TAG)"
}

function Pull-Images {
    Write-Info "Pulling latest Docker images..."
    
    Set-Location $ProjectRoot
    docker-compose -f $env:COMPOSE_FILE pull
    
    Write-Info "Images pulled successfully"
}

function Backup-Database {
    Write-Info "Creating database backup..."
    
    $BackupDir = Join-Path $ProjectRoot "backups"
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir | Out-Null
    }
    
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $BackupFile = Join-Path $BackupDir "db_backup_${Environment}_${Timestamp}.sql"
    
    try {
        docker-compose -f $env:COMPOSE_FILE exec -T postgres pg_dump -U meeting_user meeting_db | Out-File -FilePath $BackupFile -Encoding UTF8
        Write-Info "Database backed up to: $BackupFile"
    }
    catch {
        Write-Warn "Database backup failed (database might not be running yet)"
    }
}

function Deploy {
    Write-Info "Deploying to $Environment..."
    
    Set-Location $ProjectRoot
    
    # Stop old containers
    Write-Info "Stopping old containers..."
    docker-compose -f $env:COMPOSE_FILE down --remove-orphans
    
    # Start new containers
    Write-Info "Starting new containers..."
    docker-compose -f $env:COMPOSE_FILE up -d
    
    Write-Info "Deployment complete"
}

function Test-Health {
    Write-Info "Running health checks..."
    
    # Wait for services to start
    Start-Sleep -Seconds 10
    
    # Check backend health
    $MaxRetries = 30
    $RetryCount = 0
    
    while ($RetryCount -lt $MaxRetries) {
        try {
            $Response = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -TimeoutSec 5
            if ($Response.StatusCode -eq 200) {
                Write-Info "Backend health check passed"
                return $true
            }
        }
        catch {
            $RetryCount++
            Write-Warn "Health check attempt $RetryCount/$MaxRetries failed, retrying..."
            Start-Sleep -Seconds 2
        }
    }
    
    Write-Error-Custom "Health check failed after $MaxRetries attempts"
    return $false
}

function Show-Status {
    Write-Info "Service status:"
    docker-compose -f $env:COMPOSE_FILE ps
    
    Write-Info "`nRecent logs:"
    docker-compose -f $env:COMPOSE_FILE logs --tail=20
}

function Invoke-Rollback {
    Write-Error-Custom "Deployment failed, rolling back..."
    
    # Stop failed deployment
    docker-compose -f $env:COMPOSE_FILE down
    
    # Restore from backup if available
    $BackupDir = Join-Path $ProjectRoot "backups"
    $LatestBackup = Get-ChildItem -Path $BackupDir -Filter "db_backup_${Environment}_*.sql" -ErrorAction SilentlyContinue | 
                    Sort-Object LastWriteTime -Descending | 
                    Select-Object -First 1
    
    if ($LatestBackup) {
        Write-Info "Restoring database from: $($LatestBackup.FullName)"
        docker-compose -f $env:COMPOSE_FILE up -d postgres
        Start-Sleep -Seconds 5
        Get-Content $LatestBackup.FullName | docker-compose -f $env:COMPOSE_FILE exec -T postgres psql -U meeting_user meeting_db
    }
    
    Write-Error-Custom "Rollback complete. Please investigate the issue."
    exit 1
}

# Main deployment flow
function Main {
    Write-Info "Starting deployment to $Environment..."
    
    Check-Requirements
    Load-Environment
    Pull-Images
    Backup-Database
    Deploy
    
    if (Test-Health) {
        Show-Status
        Write-Info "Deployment to $Environment completed successfully!"
    }
    else {
        Invoke-Rollback
    }
}

# Run main function
Main
