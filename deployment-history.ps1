# Show deployment history and available versions
# Usage: .\deployment-history.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Flask Blog - Deployment History" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check current running version
Write-Host "Current Deployment:" -ForegroundColor Yellow
Write-Host ""

$deployPath = "C:\deployments\flask-blog"
if (Test-Path $deployPath) {
    cd $deployPath
    
    # Get current image
    try {
        $currentImage = docker inspect flask_blog_app_prod --format='{{.Config.Image}}' 2>$null
        if ($currentImage) {
            Write-Host "  Image: $currentImage" -ForegroundColor Green
        } else {
            Write-Host "  Image: Unable to determine" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Image: Unable to determine" -ForegroundColor Yellow
    }
    
    # Get container status
    $containerInfo = docker ps --filter "name=flask_blog_app_prod" --format "{{.Status}}"
    Write-Host "  Status: $containerInfo" -ForegroundColor Green
    
    # Try to get health
    try {
        $health = Invoke-WebRequest -Uri "http://localhost:5003/health" -TimeoutSec 2 -UseBasicParsing | ConvertFrom-Json
        Write-Host "  Health: $($health.status)" -ForegroundColor Green
    } catch {
        Write-Host "  Health: Unable to check" -ForegroundColor Yellow
    }
} else {
    Write-Host "  No deployment found at $deployPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "Available Versions:" -ForegroundColor Yellow
Write-Host ""

# List available local images
$images = docker images "ghcr.io/ronen-benjacob/flask-blog" --format "{{.Tag}}`t{{.CreatedAt}}`t{{.Size}}"
if ($images) {
    Write-Host "  TAG`t`t`tCREATED`t`t`t`tSIZE" -ForegroundColor Cyan
    Write-Host "  ---`t`t`t-------`t`t`t`t----" -ForegroundColor Cyan
    $images | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "  No local images found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Deployment Backups:" -ForegroundColor Yellow
Write-Host ""

# List backups
$backupPath = "C:\deployments\backups"
if (!(Test-Path $backupPath)) {
    Write-Host "  Backup directory will be created on first rollback" -ForegroundColor Yellow
    Write-Host "  Path: $backupPath" -ForegroundColor Gray
} elseif (Test-Path $backupPath) {
    $backups = Get-ChildItem $backupPath -Directory | Sort-Object CreationTime -Descending | Select-Object -First 10
    if ($backups) {
        Write-Host "  TIMESTAMP`t`t`tLOCATION" -ForegroundColor Cyan
        Write-Host "  ---------`t`t`t--------" -ForegroundColor Cyan
        foreach ($backup in $backups) {
            $timestamp = $backup.Name
            Write-Host "  $timestamp`t$($backup.FullName)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  No backups yet - backups will be created on rollback" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Commands:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Rollback to version:" -ForegroundColor White
Write-Host "    .\rollback.ps1 sha-abc1234" -ForegroundColor Gray
Write-Host ""
Write-Host "  View container logs:" -ForegroundColor White
Write-Host "    docker-compose -f $deployPath\docker-compose.prod.yml logs" -ForegroundColor Gray
Write-Host ""
Write-Host "  Check health:" -ForegroundColor White
Write-Host "    curl http://localhost:5003/health" -ForegroundColor Gray
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan