# Rollback script for Flask Blog deployment
# Usage: .\rollback.ps1 [version_tag]

param(
    [string]$Version = "latest"
)

Write-Host "=========================================" -ForegroundColor Yellow
Write-Host "Flask Blog Rollback Script" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Yellow
Write-Host ""

# Check if Docker is running
try {
    docker ps | Out-Null
} catch {
    Write-Host "ERROR: Docker is not running or not accessible" -ForegroundColor Red
    exit 1
}

# Set deployment directory
$deployPath = "C:\deployments\flask-blog"

if (!(Test-Path $deployPath)) {
    Write-Host "ERROR: Deployment directory not found: $deployPath" -ForegroundColor Red
    exit 1
}

Write-Host "Target Version: $Version" -ForegroundColor Cyan
Write-Host "Deployment Path: $deployPath" -ForegroundColor Cyan
Write-Host ""

# Create backup directory
$backupDir = "C:\deployments\backups\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "Creating backup in: $backupDir" -ForegroundColor Yellow
New-Item -Path $backupDir -ItemType Directory -Force | Out-Null

# Backup current state
Write-Host "Backing up current deployment..." -ForegroundColor Yellow
cd $deployPath
docker-compose -f docker-compose.prod.yml logs --tail=200 > "$backupDir\logs.txt"
docker-compose -f docker-compose.prod.yml ps > "$backupDir\containers.txt"
Copy-Item docker-compose.prod.yml "$backupDir\docker-compose.prod.yml.backup"
Write-Host "SUCCESS: Backup created" -ForegroundColor Green
Write-Host ""

# Stop current containers
Write-Host "Stopping current containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml down
Write-Host "SUCCESS: Containers stopped" -ForegroundColor Green
Write-Host ""

# Pull specific version
$imageName = "ghcr.io/ronen-benjacob/flask-blog:$Version"
Write-Host "Pulling Docker image: $imageName" -ForegroundColor Yellow

try {
    docker pull $imageName
    Write-Host "SUCCESS: Image pulled" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to pull image: $imageName" -ForegroundColor Red
    Write-Host "Available tags at: https://github.com/ronen-benjacob/BlogsSite/pkgs/container/flask-blog" -ForegroundColor Yellow
    
    # Restore previous state
    Write-Host ""
    Write-Host "Restoring previous state..." -ForegroundColor Yellow
    docker-compose -f docker-compose.prod.yml up -d
    exit 1
}

Write-Host ""

# Update docker-compose to use specific version
Write-Host "Updating docker-compose configuration..." -ForegroundColor Yellow
$composeContent = Get-Content docker-compose.prod.yml -Raw
$composeContent = $composeContent -replace 'ghcr\.io/ronen-benjacob/flask-blog:.*', "ghcr.io/ronen-benjacob/flask-blog:$Version"
$composeContent | Set-Content docker-compose.prod.yml
Write-Host "SUCCESS: Configuration updated" -ForegroundColor Green
Write-Host ""

# Start with rollback version
Write-Host "Starting application with version: $Version" -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml up -d
Write-Host "SUCCESS: Containers started" -ForegroundColor Green
Write-Host ""

# Wait for startup
Write-Host "Waiting for application to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Health check
Write-Host "Performing health check..." -ForegroundColor Yellow
$maxRetries = 10
$success = $false

for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5003/health" -TimeoutSec 5 -UseBasicParsing
        $content = $response.Content | ConvertFrom-Json
        
        if ($response.StatusCode -eq 200 -and $content.status -eq "healthy") {
            Write-Host "SUCCESS: Application is healthy!" -ForegroundColor Green
            $success = $true
            break
        }
    } catch {
        Write-Host "Attempt $i/$maxRetries failed. Retrying..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

Write-Host ""

if ($success) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "Rollback Successful!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Details:" -ForegroundColor Cyan
    Write-Host "  Version: $Version"
    Write-Host "  Application: http://localhost:5003"
    Write-Host "  Health: http://localhost:5003/health"
    Write-Host "  Backup: $backupDir"
    Write-Host ""
} else {
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "Rollback Failed - Health Check Failed" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Restoring from backup..." -ForegroundColor Yellow
    
    Copy-Item "$backupDir\docker-compose.prod.yml.backup" docker-compose.prod.yml -Force
    docker-compose -f docker-compose.prod.yml up -d
    
    Write-Host ""
    Write-Host "Previous version restored. Check logs:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f C:\deployments\flask-blog\docker-compose.prod.yml logs"
    Write-Host ""
    Write-Host "Backup location: $backupDir" -ForegroundColor Cyan
    exit 1
}

# Show current status
Write-Host "Current Status:" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml ps

Write-Host ""
Write-Host "Rollback complete!" -ForegroundColor Green