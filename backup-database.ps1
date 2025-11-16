# Automated Database Backup Script
# Usage: .\backup-database.ps1 [-RetentionDays 7]

param(
    [int]$RetentionDays = 7
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Database Backup Script" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$deployPath = "C:\deployments\flask-blog"
$backupPath = "C:\deployments\db-backups"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$backupPath\blog_db_$timestamp.sql"

# Create backup directory if not exists
if (!(Test-Path $backupPath)) {
    Write-Host "Creating backup directory: $backupPath" -ForegroundColor Yellow
    New-Item -Path $backupPath -ItemType Directory -Force | Out-Null
}

Write-Host "Backup Configuration:" -ForegroundColor Cyan
Write-Host "  Deployment: $deployPath"
Write-Host "  Backup Path: $backupPath"
Write-Host "  Timestamp: $timestamp"
Write-Host "  Retention: $RetentionDays days"
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

# Get database credentials from docker-compose
Write-Host "Reading database credentials..." -ForegroundColor Yellow
$dbName = "blog_db_prod"
$dbUser = "blog_user_prod"

# Perform backup
Write-Host "Creating database backup..." -ForegroundColor Yellow
Write-Host "  Database: $dbName"
Write-Host "  Output: $backupFile"
Write-Host ""

try {
    # Execute pg_dump inside the container
    docker exec $dbContainer pg_dump -U $dbUser -d $dbName > $backupFile
    
    # Check if backup file was created and has content
    if ((Test-Path $backupFile) -and (Get-Item $backupFile).Length -gt 0) {
        $fileSize = [math]::Round((Get-Item $backupFile).Length / 1MB, 2)
        Write-Host "SUCCESS: Backup created" -ForegroundColor Green
        Write-Host "  File: $backupFile"
        Write-Host "  Size: $fileSize MB"
        Write-Host ""
    } else {
        Write-Host "ERROR: Backup file is empty or not created!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR: Backup failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Compress backup
Write-Host "Compressing backup..." -ForegroundColor Yellow
try {
    Compress-Archive -Path $backupFile -DestinationPath "$backupFile.zip" -Force
    Remove-Item $backupFile
    
    $compressedSize = [math]::Round((Get-Item "$backupFile.zip").Length / 1MB, 2)
    Write-Host "SUCCESS: Backup compressed" -ForegroundColor Green
    Write-Host "  File: $backupFile.zip"
    Write-Host "  Size: $compressedSize MB"
    Write-Host ""
} catch {
    Write-Host "WARNING: Compression failed, keeping uncompressed backup" -ForegroundColor Yellow
}

# Clean up old backups
Write-Host "Cleaning up old backups (older than $RetentionDays days)..." -ForegroundColor Yellow
$cutoffDate = (Get-Date).AddDays(-$RetentionDays)
$oldBackups = Get-ChildItem $backupPath -Filter "blog_db_*.zip" | Where-Object { $_.CreationTime -lt $cutoffDate }

if ($oldBackups) {
    $deletedCount = 0
    foreach ($backup in $oldBackups) {
        Write-Host "  Deleting: $($backup.Name)" -ForegroundColor Gray
        Remove-Item $backup.FullName -Force
        $deletedCount++
    }
    Write-Host "SUCCESS: Deleted $deletedCount old backup(s)" -ForegroundColor Green
} else {
    Write-Host "  No old backups to delete" -ForegroundColor Gray
}

Write-Host ""

# List current backups
Write-Host "Current Backups:" -ForegroundColor Cyan
$backups = Get-ChildItem $backupPath -Filter "blog_db_*.zip" | Sort-Object CreationTime -Descending | Select-Object -First 10

if ($backups) {
    Write-Host ""
    Write-Host "  TIMESTAMP`t`t`tSIZE`t`tAGE" -ForegroundColor Cyan
    Write-Host "  ---------`t`t`t----`t`t---" -ForegroundColor Cyan
    foreach ($backup in $backups) {
        $size = [math]::Round($backup.Length / 1MB, 2)
        $age = [math]::Round((New-TimeSpan -Start $backup.CreationTime -End (Get-Date)).TotalDays, 1)
        $timestamp = $backup.Name -replace 'blog_db_', '' -replace '.sql.zip', ''
        Write-Host "  $timestamp`t$size MB`t`t$age days" -ForegroundColor Gray
    }
} else {
    Write-Host "  No backups found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Backup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backup Location: $backupPath" -ForegroundColor Cyan
Write-Host "Latest Backup: $backupFile.zip" -ForegroundColor Cyan
Write-Host ""