# PowerShell script to run frontend in development mode

Write-Host "Starting Sign Language Video Call Frontend..." -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""

# Check if Node.js is installed
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check Node version
$nodeVersion = node --version
$npmVersion = npm --version
Write-Host "Node version: $nodeVersion" -ForegroundColor Cyan
Write-Host "npm version: $npmVersion" -ForegroundColor Cyan

# Check if node_modules exists
if (!(Test-Path "node_modules")) {
    Write-Host "node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    npm ci
}

Write-Host ""
Write-Host "Frontend starting on http://localhost:5173" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Run dev server
npm run dev
