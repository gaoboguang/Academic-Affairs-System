$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$DataDir = Join-Path $RootDir "data"
$BackupDir = Join-Path $DataDir "backups"

if (-not (Test-Path $BackupDir)) {
  New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ArchivePath = Join-Path $BackupDir "local_edu_backup_$Timestamp.zip"

Compress-Archive -Path (Join-Path $DataDir "*") -DestinationPath $ArchivePath -Force
Write-Host "备份完成: $ArchivePath"

