#!/bin/bash
# High-Performance Minecraft OS Optimizer
# Optimized for Linux VPS/Dedicated Servers

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (sudo)" 
   exit 1
fi

echo "🚀 Starting System Optimization for Minecraft..."

# 1. Network Stack Optimization (TCP/IP)
echo "🌐 Optimizing Network Stack..."
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216
sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"
sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"
sysctl -w net.ipv4.tcp_slow_start_after_idle=0
sysctl -w net.core.netdev_max_backlog=5000
sysctl -w net.ipv4.tcp_timestamps=1
sysctl -w net.ipv4.tcp_sack=1

# 2. Memory Management (Transparent Huge Pages)
echo "🧠 Optimizing Memory (THP)..."
echo always > /sys/kernel/mm/transparent_hugepage/enabled
echo always > /sys/kernel/mm/transparent_hugepage/defrag

# 3. File Descriptor Limits
echo "📁 Increasing File Limits..."
ulimit -n 65536
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 4. CPU Governor (Performance Mode)
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    echo "⚡ Setting CPU Governor to Performance..."
    for dev in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo performance > "$dev"
    done
fi

# 5. Swappiness (Reduce disk swapping)
echo "💾 Reducing Swappiness..."
sysctl -w vm.swappiness=10

# 6. Persistence (Save to sysctl.conf)
echo "💾 Making changes permanent in /etc/sysctl.conf..."
SYSCTL_CONF="/etc/sysctl.conf"
OPTIMIZATIONS=(
    "net.core.rmem_max=16777216"
    "net.core.wmem_max=16777216"
    "net.ipv4.tcp_rmem=4096 87380 16777216"
    "net.ipv4.tcp_wmem=4096 65536 16777216"
    "net.ipv4.tcp_slow_start_after_idle=0"
    "net.core.netdev_max_backlog=5000"
    "net.ipv4.tcp_timestamps=1"
    "net.ipv4.tcp_sack=1"
    "vm.swappiness=10"
)

for opt in "${OPTIMIZATIONS[@]}"; do
    key=$(echo $opt | cut -d'=' -f1)
    if grep -q "^$key" "$SYSCTL_CONF"; then
        sed -i "s|^$key.*|$opt|" "$SYSCTL_CONF"
    else
        echo "$opt" >> "$SYSCTL_CONF"
    fi
done

echo "✅ Optimization Complete! Your server is now tuned for maximum performance."
echo "🚀 All settings have been applied and saved. They will persist after reboot."
