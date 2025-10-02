#!/bin/bash
# Additional security hardening

set -euo pipefail

echo "Applying security hardening..."

# SSH hardening
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/X11Forwarding yes/X11Forwarding no/' /etc/ssh/sshd_config
echo "AllowUsers deploy" >> /etc/ssh/sshd_config
systemctl restart sshd

# Kernel hardening
cat >> /etc/sysctl.d/99-security.conf <<EOF
kernel.exec-shield = 1
kernel.randomize_va_space = 2
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_source_route = 0
EOF
sysctl -p /etc/sysctl.d/99-security.conf

echo "Security hardening complete!"