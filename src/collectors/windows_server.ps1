# iqData Bot - Windows Server Data Collector
# Collects system information, disk status, services, and installed roles
# Usage: .\windows_server.ps1 [-OutputPath <path>]

param(
    [string]$OutputPath = ".\collected_data"
)

$ErrorActionPreference = "SilentlyContinue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$hostname = $env:COMPUTERNAME
$outputFile = Join-Path $OutputPath "${hostname}_server_${timestamp}.txt"

if (!(Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

function Write-Section($title) {
    "`n$('=' * 60)" | Out-File -FilePath $outputFile -Append -Encoding utf8
    "  $title" | Out-File -FilePath $outputFile -Append -Encoding utf8
    "$('=' * 60)" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "SYSTEM INFORMATION"
systeminfo | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "PROCESSORS"
Get-WmiObject -Class Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | Format-List | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "MEMORY"
Get-WmiObject -Class Win32_PhysicalMemory | Select-Object Capacity, Speed, Manufacturer | Format-List | Out-File -FilePath $outputFile -Append -Encoding utf8
$totalRam = (Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB
"Total Physical Memory: $([math]::Round($totalRam, 2)) GB" | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "DISK STATUS"
Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $sizeGB = [math]::Round($_.Size / 1GB, 2)
    $freeGB = [math]::Round($_.FreeSpace / 1GB, 2)
    $usedPct = if ($_.Size -gt 0) { [math]::Round(($_.Size - $_.FreeSpace) / $_.Size * 100, 1) } else { 0 }
    "Drive $($_.DeviceID) - Total: ${sizeGB} GB, Used: $([math]::Round($sizeGB - $freeGB, 2)) GB, Free: ${freeGB} GB (${usedPct}% used)"
} | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "RAID STATUS (diskpart)"
try {
    $raidOutput = diskpart /s (Join-Path $env:TEMP "diskpart_list.txt")
    "list disk" | Out-File -FilePath (Join-Path $env:TEMP "diskpart_list.txt") -Encoding ascii
    $raidOutput | Out-File -FilePath $outputFile -Append -Encoding utf8
} catch {
    "diskpart not available" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "NETWORK INTERFACES"
Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, MacAddress, LinkSpeed | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
Get-NetIPAddress | Where-Object {$_.AddressFamily -eq 'IPv4'} | Select-Object InterfaceAlias, IPAddress, PrefixLength | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "INSTALLED ROLES AND FEATURES"
try {
    Get-WindowsFeature | Where-Object {$_.Installed -eq $true} | Select-Object Name, DisplayName | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
} catch {
    "Get-WindowsFeature not available" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "SERVICES"
Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object Name, DisplayName | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "VIRTUALIZATION STATUS"
try {
    $hyperv = Get-WindowsFeature -Name Hyper-V
    "Hyper-V Installed: $($hyperv.Installed)" | Out-File -FilePath $outputFile -Append -Encoding utf8
    if ($hyperv.Installed) {
        Get-VMHost | Select-Object Name, VirtualMachineMigrationEnabled | Format-List | Out-File -FilePath $outputFile -Append -Encoding utf8
        Get-VM | Select-Object Name, State, @{N="MemoryGB";E={[math]::Round($_.MemoryAssigned/1GB,2)}}, ProcessorCount | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
    }
} catch {
    "Hyper-V check failed" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "WINDOWS BACKUP STATUS"
try {
    wbadmin get versions 2>&1 | Out-File -FilePath $outputFile -Append -Encoding utf8
} catch {
    "wbadmin not available" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "VSS SHADOW COPIES"
try {
    vssadmin list shadows 2>&1 | Out-File -FilePath $outputFile -Append -Encoding utf8
} catch {
    "vssadmin not available" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "WINDOWS UPDATE"
try {
    $hotfixes = Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10
    $hotfixes | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
} catch {
    "Get-HotFix not available" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "HOSTED SERVICES (IIS)"
try {
    $iis = Get-WindowsFeature -Name Web-Server
    if ($iis.Installed) {
        Import-Module WebAdministration
        Get-Website | Select-Object Name, State, PhysicalPath, Bindings | Format-List | Out-File -FilePath $outputFile -Append -Encoding utf8
    }
} catch {
    "IIS not available" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "SQL SERVER"
try {
    $sqlService = Get-Service -Name "MSSQL*" -ErrorAction SilentlyContinue
    if ($sqlService) {
        $sqlService | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
    }
} catch {
    "SQL Server check failed" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "COLLECTION COMPLETE"
"Data collected at $(Get-Date)" | Out-File -FilePath $outputFile -Append -Encoding utf8
"Output file: $outputFile" | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Host "Data collected successfully: $outputFile"
