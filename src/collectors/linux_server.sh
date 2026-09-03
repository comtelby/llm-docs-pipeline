#!/bin/bash
# iqData Bot - Linux Server Data Collector
# Collects system information, disk status, services, and configurations
# Usage: ./linux_server.sh [output_path]

set -e

OUTPUT_PATH="${1:-./collected_data}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
HOSTNAME=$(hostname)
OUTPUT_FILE="${OUTPUT_PATH}/${HOSTNAME}_server_${TIMESTAMP}.txt"

mkdir -p "$OUTPUT_PATH"

write_section() {
    echo "" >> "$OUTPUT_FILE"
    echo "============================================================" >> "$OUTPUT_FILE"
    echo "  $1" >> "$OUTPUT_FILE"
    echo "============================================================" >> "$OUTPUT_FILE"
}

write_section "SYSTEM INFORMATION"
echo "Hostname: $(hostname)" >> "$OUTPUT_FILE"
echo "Kernel: $(uname -a)" >> "$OUTPUT_FILE"
echo "OS: $(cat /etc/os-release 2>/dev/null || cat /etc/redhat-release 2>/dev/null)" >> "$OUTPUT_FILE"
echo "Uptime: $(uptime)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

write_section "CPU INFORMATION"
lscpu >> "$OUTPUT_FILE" 2>/dev/null || cat /proc/cpuinfo >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "MEMORY INFORMATION"
free -h >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
cat /proc/meminfo | head -20 >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "DISK STATUS"
df -h >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
echo "--- Block Devices ---" >> "$OUTPUT_FILE"
lsblk -f >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
echo "--- Partition Table ---" >> "$OUTPUT_FILE"
fdisk -l >> "$OUTPUT_FILE" 2>/dev/null || parted -l >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "RAID STATUS"
cat /proc/mdstat >> "$OUTPUT_FILE" 2>/dev/null || echo "No software RAID found" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
if command -v mdadm &> /dev/null; then
    mdadm --detail --scan >> "$OUTPUT_FILE" 2>/dev/null
fi
echo "" >> "$OUTPUT_FILE"

write_section "NETWORK INTERFACES"
ip addr show >> "$OUTPUT_FILE" 2>/dev/null || ifconfig -a >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
echo "--- Routing Table ---" >> "$OUTPUT_FILE"
ip route show >> "$OUTPUT_FILE" 2>/dev/null || route -n >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"
echo "--- DNS Configuration ---" >> "$OUTPUT_FILE"
cat /etc/resolv.conf >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "FIREWALL STATUS"
iptables -L -n >> "$OUTPUT_FILE" 2>/dev/null || echo "iptables not available" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

write_section "RUNNING SERVICES"
systemctl list-units --type=service --state=running >> "$OUTPUT_FILE" 2>/dev/null || service --status-all >> "$OUTPUT_FILE" 2>/dev/null
echo "" >> "$OUTPUT_FILE"

write_section "VIRTUALIZATION STATUS"
if command -v virsh &> /dev/null; then
    echo "--- KVM/QEMU VMs ---" >> "$OUTPUT_FILE"
    virsh list --all >> "$OUTPUT_FILE" 2>/dev/null
elif command -v docker &> /dev/null; then
    echo "--- Docker Containers ---" >> "$OUTPUT_FILE"
    docker ps -a >> "$OUTPUT_FILE" 2>/dev/null
fi
echo "" >> "$OUTPUT_FILE"

write_section "VMWARE ESXI (if applicable)"
if command -v esxcli &> /dev/null; then
    esxcli system version get >> "$OUTPUT_FILE" 2>/dev/null
    esxcli hardware cpu list >> "$OUTPUT_FILE" 2>/dev/null
    esxcli hardware memory get >> "$OUTPUT_FILE" 2>/dev/null
    esxcli storage core device list >> "$OUTPUT_FILE" 2>/dev/null
else
    echo "Not running on ESXi" >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

write_section "DOCKER/CONTAINERS"
if command -v docker &> /dev/null; then
    docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" >> "$OUTPUT_FILE" 2>/dev/null
else
    echo "Docker not installed" >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

write_section "PYTHON/NODE VERSIONS"
python3 --version >> "$OUTPUT_FILE" 2>/dev/null || echo "Python3 not found" >> "$OUTPUT_FILE"
node --version >> "$OUTPUT_FILE" 2>/dev/null || echo "Node not found" >> "$OUTPUT_FILE"
java -version 2>&1 >> "$OUTPUT_FILE" 2>/dev/null || echo "Java not found" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

write_section "CRON JOBS"
crontab -l >> "$OUTPUT_FILE" 2>/dev/null || echo "No crontab" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

write_section "LOG FILES (recent errors)"
journalctl --since "7 days ago" -p err --no-pager | tail -50 >> "$OUTPUT_FILE" 2>/dev/null || \
    grep -i "error\|fail\|critical" /var/log/syslog 2>/dev/null | tail -50 >> "$OUTPUT_FILE" 2>/dev/null || \
    echo "No recent errors found" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

write_section "COLLECTION COMPLETE"
echo "Data collected at $(date)" >> "$OUTPUT_FILE"
echo "Output file: $OUTPUT_FILE" >> "$OUTPUT_FILE"

echo "Data collected successfully: $OUTPUT_FILE"
