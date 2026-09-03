# iqData Bot - Hyper-V Data Collector
# Collects Hyper-V host information, VMs, clusters, and storage
# Usage: .\hyper_v.ps1 [-OutputPath <path>]

param(
    [string]$OutputPath = ".\collected_data"
)

$ErrorActionPreference = "SilentlyContinue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$hostname = $env:COMPUTERNAME
$outputFile = Join-Path $OutputPath "${hostname}_hyperv_${timestamp}.txt"

if (!(Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

function Write-Section($title) {
    "`n$('=' * 60)" | Out-File -FilePath $outputFile -Append -Encoding utf8
    "  $title" | Out-File -FilePath $outputFile -Append -Encoding utf8
    "$('=' * 60)" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "HYPER-V HOST INFORMATION"
Get-VMHost | Select-Object Name, ComputerName, Version, OperatingSystem, VirtualMachineMigrationEnabled, NumaSpanningEnabled | Format-List | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "PHYSICAL HOST HARDWARE"
Get-WmiObject -Class Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | Format-List | Out-File -FilePath $outputFile -Append -Encoding utf8
$totalRam = [math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
"Total RAM: $totalRam GB" | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "VIRTUAL MACHINES"
Get-VM | Select-Object Name, State, @{N="MemoryGB";E={[math]::Round($_.MemoryAssigned/1GB,2)}}, ProcessorCount, @{N="Uptime";E={$_.Uptime}}, Generation | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "VM DISKS"
Get-VM | Get-VMHardDiskDrive | Select-Object VMName, ControllerType, ControllerNumber, Path | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "VM NETWORK ADAPTERS"
Get-VM | Get-VMNetworkAdapter | Select-Object VMName, Name, SwitchName, MacAddress, IPAddresses | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "VM SNAPSHOTS"
Get-VM | ForEach-Object {
    $snaps = Get-VMSnapshot -VMName $_.Name -ErrorAction SilentlyContinue
    if ($snaps) {
        "VM: $($_.Name)" | Out-File -FilePath $outputFile -Append -Encoding utf8
        $snaps | Select-Object Name, CreationTime, @{N="SizeGB";E={[math]::Round($_.Size/1GB,2)}} | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
    }
}

Write-Section "VSWITCHES"
Get-VMSwitch | Select-Object Name, SwitchType, AllowManagementOS, NetAdapterInterfaceDescription | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Section "STORAGE POOLS"
try {
    Get-StoragePool | Select-Object FriendlyName, HealthStatus, OperationalStatus, SizeRemaining, Size | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
} catch {
    "StoragePool not available" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "CLUSTER STATUS"
try {
    Get-ClusterNode | Select-Object Name, State, NodeWeight | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
    Get-ClusterResource | Select-Object Name, OwnerGroup, ResourceType, State | Format-Table -AutoSize | Out-File -FilePath $outputFile -Append -Encoding utf8
} catch {
    "Failover Clustering not configured" | Out-File -FilePath $outputFile -Append -Encoding utf8
}

Write-Section "COLLECTION COMPLETE"
"Data collected at $(Get-Date)" | Out-File -FilePath $outputFile -Append -Encoding utf8

Write-Host "Hyper-V data collected successfully: $outputFile"
