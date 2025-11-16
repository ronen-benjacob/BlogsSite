# Database Restore Script
# Usage: .\restore-database.ps1 -BackupFile "C:\deployments\db-backups\blog_db_20251116_140530.sql.zip"

param(
    [Parameter(Mandatory=$false)]
    [string]$BackupFile
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Yellow
Write-Host "Database Restore Script" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Yellow
Write-Host ""

# Configuration
$deployPath = "C:\deployments\flask-blog"
$backupPath = "C:\deployments\db-backups"
$dbName = "blog_db_prod"
$dbUser = "blog_user_prod"

# If no backup file specified, list available backups
if (!$BackupFile) {
    Write-Host "Available Backups:" -ForegroundColor Cyan
    Write-Host ""
    
    $backups = Get-ChildItem $backupPath -Filter "blog_db_*.zip" | Sort-Object CreationTime -Descending
    
    if ($backups) {
        $i = 1
        foreach ($backup in $backups) {
            $size = [math]::Round($backup.Length / 1MB, 2)
            $age = [math]::Round((New-TimeSpan -Start $backup.CreationTime -End (Get-Date)).TotalHours, 1)
            Write-Host "  [$i] $($backup.Name)" -ForegroundColor White
            Write-Host "      Size: $size MB | Age: $age hours | Path: $($backup.FullName)" -ForegroundColor Gray
            Write-Host ""
            $i++
        }
        
        Write-Host "Usage: .\restore-database.ps1 -BackupFile 'PATH_TO_BACKUP'" -ForegroundColor Yellow
        Write-Host "Example: .\restore-database.ps1 -BackupFile '$($backups[0].FullName)'" -ForegroundColor Yellow
    } else {
        Write-Host "  No backups found in $backupPath" -ForegroundColor Yellow
    }
    
    exit 0
}

# Validate backup file
if (!(Test-Path $BackupFile)) {
    Write-Host "ERROR: Backup file not found: $BackupFile" -ForegroundColor Red
    exit 1
}

Write-Host "Restore Configuration:" -ForegroundColor Cyan
Write-Host "  Backup File: $BackupFile"
Write-Host "  Database: $dbName"
Write-Host "  User: $dbUser"
Write-Host ""

# Check if containers are running
Write-Host "Checking database container..." -ForegroundColor Yellow
$dbContainer = docker ps --filter "name=flask_blog_db" --format "{{.Names}}"

if (!$dbContainer) {
    Write-Host "ERROR: Database container is not running!" -ForegroundColor Red
    Write-Host "Start containers with: docker-compose -f $deployPath\docker-compose.prod.yml up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "SUCCESS: Database container found: $dbContainer" -ForegroundColor Green
Write-Host ""

# Warning confirmation
Write-Host "⚠️  WARNING: This will REPLACE all current database data!" -ForegroundColor Red
Write-Host ""
$confirmation = Read-Host "Type 'yes' to continue"

if ($confirmation -ne "yes") {
    Write-Host "Restore cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# Extract backup if compressed
$sqlFile = $BackupFile
if ($BackupFile -like "*.zip") {
    Write-Host "Extracting backup..." -ForegroundColor Yellow
    $tempDir = "$env:TEMP\db-restore-$(Get-Date -Format 'yyyyMMddHHmmss')"
    New-Item -Path $tempDir -ItemType Directory -Force | Out-Null
    
    Expand-Archive -Path $BackupFile -DestinationPath $tempDir -Force
    $sqlFile = Get-ChildItem $tempDir -Filter "*.sql" | Select-Object -First 1 -ExpandProperty FullName
    
    if (!$sqlFile) {
        Write-Host "ERROR: No SQL file found in backup archive!" -ForegroundColor Red
        Remove-Item $tempDir -Recurse -Force
        exit 1
    }
    
    Write-Host "SUCCESS: Extracted to $sqlFile" -ForegroundColor Green
    Write-Host ""
}

# Create backup of current database before restore
Write-Host "Creating safety backup of current database..." -ForegroundColor Yellow
$safetyBackup = "$backupPath\blog_db_before_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
docker exec $dbContainer pg_dump -U $dbUser -d $dbName > $safetyBackup

if ((Test-Path $safetyBackup) -and (Get-Item $safetyBackup).Length -gt 0) {
    Write-Host "SUCCESS: Safety backup created: $safetyBackup" -ForegroundColor Green
} else {
    Write-Host "WARNING: Could not create safety backup!" -ForegroundColor Yellow
}
Write-Host ""

# Stop web application
Write-Host "Stopping web application..." -ForegroundColor Yellow
docker-compose -f $deployPath\docker-compose.prod.yml stop web
Write-Host ""

# Restore database
Write-Host "Restoring database..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..."
Write-Host ""

try {
    # Drop and recreate database
    docker exec $dbContainer psql -U $dbUser -d postgres -c "DROP DATABASE IF EXISTS $dbName;"
    docker exec $dbContainer psql -U $dbUser -d postgres -c "CREATE DATABASE $dbName;"
    
    # Restore from backup
    Get-Content $sqlFile | docker exec -i $dbContainer psql -U $dbUser -d $dbName
    
    Write-Host "SUCCESS: Database restored!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "ERROR: Restore failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Safety backup available at: $safetyBackup" -ForegroundColor Yellow
    exit 1
} finally {
    # Clean up temp files
    if ($BackupFile -like "*.zip" -and (Test-Path $tempDir)) {
        Remove-Item $tempDir -Recurse -Force
    }
}

# Restart web application
Write-Host "Restarting web application..." -ForegroundColor Yellow
docker-compose -f $deployPath\docker-compose.prod.yml start web
Start-Sleep -Seconds 5
Write-Host ""

# Verify restore
Write-Host "Verifying restore..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5003/health" -TimeoutSec 10 -UseBasicParsing
    $health = $response.Content | ConvertFrom-Json
    
    if ($health.status -eq "healthy") {
        Write-Host "SUCCESS: Application is healthy!" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Application health check returned: $($health.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNING: Could not verify application health" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Restore Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Restored from: $BackupFile" -ForegroundColor Cyan
Write-Host "Safety backup: $safetyBackup" -ForegroundColor Cyan
Write-Host ""