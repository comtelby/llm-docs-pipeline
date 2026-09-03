#!/bin/bash
# iqData Bot - VMware ESXi Data Collector
# Collects ESXi host information, VMs, storage, and networking
# Usage: ./vmware_esxi.sh [output_path]

set -e

OUTPUT_PATH="${1:-./collected_data}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
HOSTNAME=$(hostname)
OUTPUT_FILE="${OUTPUT_PATH}/${HOSTNAME}_esxi_${TIMESTAMP}.txt"

mkdir -p "$OUTPUT_PATH"

write_section() {
    echo "" >> "$OUTPUT_FILE"
    echo "============================================================" >> "$OUTPUT_FILE"
    echo "  $1" >> "$OUTPUT_FILE"
    echo "============================================================" >> "$OUTPUT_FILE"
}

write_section "ESXi VERSION"
esxcli system version get >> "$OUTPUT_FILE" 2>/dev/null
vmware -v >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "HARDWARE INFO"
esxcli hardware cpu list >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
esxcli hardware memory get >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
esxcli hardware platform get >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "NETWORKING"
esxcli network nic list >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
esxcli network vswitch standard list >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
esxcli network ip interface list >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
esxcli network ip interface ipv4 get >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "STORAGE"
esxcli storage core device list >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
esxcli storage filesystem list >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
esxcli storage nmp device list >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "VIRTUAL MACHINES"
vim-cmd vmsvc/getallvms >> "$OUTPUT_FILE" 2>/dev/null || esxcli vm list >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "DATASTORES"
esxcli storage filesystem volume list >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "SNAPSHOTS"
for vmid in $(vim-cmd vmsvc/getallvms 2>/dev/null | awk '{print $1}' | grep -E '^[0-9]+$'); do
    snap=$(vim-cmd vmsvc/snapshot.get $vmid 2>/dev/null)
    if echo "$snap" | grep -q "Snapshot"; then
        echo "VM ID $vmid has snapshots:" >> "$OUTPUT_FILE"
        echo "$snap" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
done
echo "" >> "$OUTPUT_FILE"

write_section "HA/DRS STATUS"
vim-cmd ha/hostsvc/ha/get_config >> "$OUTPUT_FILE" 2>/dev/null || echo "HA config not available via CLI" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

write_section "SERVICES"
esxcli system syslog config get >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
esxcli system ntp get >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
esxcli system security fips140 rnod get >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "LICENSES"
vim-cmd vimsvc/auth/validate_license >> "$OUTPUT_FILE" 2>/dev/null || echo "License info not available" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

write_section "COLLECTION COMPLETE"
echo "Data collected at $(date)" >> "$OUTPUT_FILE"
echo "Output file: $OUTPUT_FILE" >> "$OUTPUT_FILE"

echo "ESXi data collected successfully: $OUTPUT_FILE"
