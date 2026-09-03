# iqData Bot - Backup System Data Collector (Veeam/Acronis/Windows Backup)
# Collects backup job history, repository info, and scheduling
# Usage: .\backup_collect.ps1 [-OutputPath <path>]

param(
    [string]$OutputPath = ".\collected_data"
)

$ErrorActionPreference = "SilentlyContinue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$hostname = $env:COMPUTERNAME
$outputFile = Join-Path $OutputPath "${hostname}_backup_${timestamp}.txt"

if (!(Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

function Write-Section($title) {
    "`n$('=' * 60)" | Out-File -FilePath $outputFile -Append -Encoding utf8
    "  $title" | Out-File -FilePath $outputFile -Append -Encoding utf8
    "$('=' * 60)" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "BACKUP SOFTWARE DETECTION"
$veeam = Get-Service -Name "Veeam*" -ErrorAction SilentlyContinue
$acronis = Get-Service -Name "Acronis*" -ErrorAction SilentlyContinue
if ($veeam) {
    "Veeam Backup & Replication detected" | Out-File -FilePath $outputFile -Append -Encoding utf8
    $veeam | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
}
if ($acronis) {
    "Acronis Cyber Protect detected" | Out-File -FilePath $outputFile -Append -Encoding utf8
    $acronis | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
}
if (!$veeam -and !$acronis) {
    "No third-party backup software detected, checking Windows Backup..." | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "WINDOWS SERVER BACKUP"
try {
    wbadmin get versions 2>&1 | Out-File -FilePath $outputFile -Append -Encoding utf8
    wbadmin get jobs 2>&1 | Out-File -FilePath $outputFile -Append -Encoding utf8
} catch {
    "Windows Server Backup not available" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "VSS SHADOW COPIES"
try {
    vssadmin list shadows 2>&1 | Out-File -FilePath $outputFile -Append -Encoding utf8
    vssadmin list writers 2>&1 | Out-File -FilePath $outputFile -Append -Encoding utf8
} catch {
    "vssadmin not available" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "BACKUP REPOSITORY DISK STATUS"
Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $sizeGB = [math]::Round($_.Size / 1GB, 2)
    $freeGB = [math]::Round($_.FreeSpace / 1GB, 2)
    "Drive $($_.DeviceID) - Total: ${sizeGB} GB, Free: ${freeGB} GB ($([math]::Round($freeGB/$sizeGB*100,1))% free)"
} | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "VEEAM BACKUP JOBS (via PowerShell Module)"
try {
    if (Get-Module -ListAvailable -Name Veeam.Backup.PowerShell) {
        Import-Module Veeam.Backup.PowerShell
        Get-VBRJob | Select-Object Name, JobType, LastState, LastRun, ScheduleEnabled | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
        Get-VBRBackup | Select-Object Name, JobName, CreationTime, @{N="SizeGB";E={[math]::Round($_.Stats.BackupSize/1GB,2)}} | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
    } else {
        "Veeam PowerShell module not available" | Out-File -FilePath $outputFile -Append -Encoding utf8
    }
} catch {
    "Veeam job collection failed" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "SCHEDULED TASKS (Backup related)"
Get-ScheduledTask | Where-Object {$_.TaskName -match "backup|veeam|acronis|shadow"} | Select-Object TaskName, State, @{N="NextRun";E={$_.NextRunTime}} | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "COLLECTION COMPLETE"
"Data collected at $(Get-Date)" | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Host "Backup data collected successfully: $outputFile"
