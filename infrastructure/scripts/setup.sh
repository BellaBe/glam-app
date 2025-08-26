#!/bin/bash
# ================================================================================
# GLAM You Up - Vultr VM Setup Script
# FILE: infrastructure/scripts/setup.sh
# 
# Description: Complete server initialization for Ubuntu 22.04 LTS on Vultr
# Run as: root user on fresh VM instance
# Usage: bash setup.sh
# ================================================================================

set -euo pipefail

# ================================================================================
# CONFIGURATION
# ================================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() { echo -e "${GREEN}[$(date +'%H:%M:%S')] ✓${NC} $1"; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] ✗${NC} $1" >&2; exit 1; }
warn() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠${NC} $1"; }
info() { echo -e "${BLUE}[$(date +'%H:%M:%S')] ℹ${NC} $1"; }

# System requirements
MIN_MEMORY_GB=8
MIN_DISK_GB=50
SWAP_SIZE_GB=4

# Versions
DOCKER_COMPOSE_VERSION="2.24.0"
NODE_EXPORTER_VERSION="1.7.0"

# ================================================================================
# PRE-FLIGHT CHECKS
# ================================================================================

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root. Use: sudo bash setup.sh"
fi

# Check Ubuntu version
if ! grep -q "Ubuntu 22.04" /etc/os-release; then
    warn "This script is designed for Ubuntu 22.04 LTS. Current OS:"
    cat /etc/os-release | grep PRETTY_NAME
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# Check system resources
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
TOTAL_DISK=$(df -BG / | awk 'NR==2 {print int($2)}')

info "System Resources:"
info "  Memory: ${TOTAL_MEM}GB (Required: ${MIN_MEMORY_GB}GB)"
info "  Disk: ${TOTAL_DISK}GB (Required: ${MIN_DISK_GB}GB)"

if [[ $TOTAL_MEM -lt $MIN_MEMORY_GB ]]; then
    error "Insufficient memory. Required: ${MIN_MEMORY_GB}GB, Available: ${TOTAL_MEM}GB"
fi

if [[ $TOTAL_DISK -lt $MIN_DISK_GB ]]; then
    warn "Low disk space. Recommended: ${MIN_DISK_GB}GB, Available: ${TOTAL_DISK}GB"
fi

echo "=================================================================================="
echo "                    GLAM You Up - Production Server Setup"
echo "=================================================================================="
echo ""

# ================================================================================
# SYSTEM UPDATE & ESSENTIAL PACKAGES
# ================================================================================

log "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y -o Dpkg::Options::="--force-confold"

log "Installing essential packages..."
apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    make \
    jq \
    ufw \
    fail2ban \
    unattended-upgrades \
    python3-pip \
    certbot \
    python3-certbot-nginx \
    restic \
    zip \
    unzip

# ================================================================================
# SECURITY HARDENING - STAGE 1: FIREWALL
# ================================================================================

log "Configuring UFW firewall..."

# Reset firewall to defaults
ufw --force disable
ufw --force reset

# Configure firewall rules
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Enable firewall
ufw --force enable
log "Firewall enabled with ports 22, 80, 443 open"

# ================================================================================
# SECURITY HARDENING - STAGE 2: FAIL2BAN
# ================================================================================

log "Configuring fail2ban..."

cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
destemail = admin@localhost
sender = fail2ban@localhost
action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2

[nginx-noproxy]
enabled = true
port = http,https
filter = nginx-noproxy
logpath = /var/log/nginx/error.log
maxretry = 2
EOF

systemctl enable fail2ban
systemctl restart fail2ban
log "fail2ban configured and started"

# ================================================================================
# SECURITY HARDENING - STAGE 3: AUTOMATIC UPDATES
# ================================================================================

log "Configuring automatic security updates..."

cat > /etc/apt/apt.conf.d/50unattended-upgrades <<'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";
EOF

cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

systemctl enable unattended-upgrades
log "Automatic security updates enabled"

# ================================================================================
# DOCKER INSTALLATION
# ================================================================================

log "Installing Docker..."

# Remove old Docker installations
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Verify Docker installation
docker --version || error "Docker installation failed"
log "Docker installed successfully"

# ================================================================================
# DOCKER COMPOSE INSTALLATION
# ================================================================================

log "Installing Docker Compose..."

# Download Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version || error "Docker Compose installation failed"
log "Docker Compose ${DOCKER_COMPOSE_VERSION} installed"

# ================================================================================
# SYSTEM OPTIMIZATION
# ================================================================================

log "Optimizing system settings..."

# Increase file limits
cat >> /etc/security/limits.conf <<'EOF'

# GLAM You Up Limits
* soft nofile 65535
* hard nofile 65535
* soft nproc 32768
* hard nproc 32768
root soft nofile 65535
root hard nofile 65535
EOF

# Optimize kernel parameters
cat > /etc/sysctl.d/99-glam-optimization.conf <<'EOF'
# Network optimizations
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_tw_buckets = 1440000
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15
net.ipv4.ip_local_port_range = 10000 65000

# Memory optimizations
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File system optimizations
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288
fs.inotify.max_queued_events = 32768
EOF

# Security kernel parameters
cat > /etc/sysctl.d/99-glam-security.conf <<'EOF'
# Security settings
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

# Apply sysctl settings
sysctl -p /etc/sysctl.d/99-glam-optimization.conf
sysctl -p /etc/sysctl.d/99-glam-security.conf
log "System optimization complete"

# ================================================================================
# CREATE DEPLOY USER
# ================================================================================

log "Creating deploy user..."

# Create deploy user if not exists
if ! id -u deploy &>/dev/null; then
    useradd -m -s /bin/bash deploy
    log "Deploy user created"
else
    log "Deploy user already exists"
fi

# Add deploy user to docker group
usermod -aG docker deploy

# Setup SSH directory
mkdir -p /home/deploy/.ssh
touch /home/deploy/.ssh/authorized_keys
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh

# Allow deploy user sudo access for specific commands
cat > /etc/sudoers.d/deploy <<'EOF'
# Deploy user sudo permissions
deploy ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker-compose, /usr/bin/docker-compose, /usr/bin/make, /bin/systemctl restart docker, /usr/bin/certbot
EOF

log "Deploy user configured with Docker access"

# ================================================================================
# CREATE APPLICATION DIRECTORIES
# ================================================================================

log "Creating application directories..."

# Create directory structure
mkdir -p /opt/glam/{infrastructure,logs,backups}
mkdir -p /opt/glam/infrastructure/{nginx,configs,scripts}
mkdir -p /var/backups/glam
mkdir -p /var/log/glam
mkdir -p /var/www/certbot

# Set permissions
chown -R deploy:deploy /opt/glam
chown -R deploy:deploy /var/backups/glam
chown -R deploy:deploy /var/log/glam
chmod 755 /opt/glam
chmod 755 /var/backups/glam

log "Application directories created"

# ================================================================================
# SETUP SWAP SPACE
# ================================================================================

log "Configuring swap space..."

# Check if swap already exists
if [ ! -f /swapfile ]; then
    # Create swap file
    fallocate -l ${SWAP_SIZE_GB}G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # Make swap permanent
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    
    log "Created ${SWAP_SIZE_GB}GB swap file"
else
    CURRENT_SWAP=$(free -g | awk '/^Swap:/{print $2}')
    log "Swap already configured (${CURRENT_SWAP}GB)"
fi

# ================================================================================
# INSTALL MONITORING TOOLS
# ================================================================================

log "Installing monitoring tools..."

# Install Node Exporter for Prometheus monitoring
if [ ! -f /usr/local/bin/node_exporter ]; then
    wget -q https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
    tar xzf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
    mv node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/
    rm -rf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64*
    
    # Create systemd service
    cat > /etc/systemd/system/node_exporter.service <<'EOF'
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=nobody
Group=nogroup
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable node_exporter
    systemctl start node_exporter
    log "Node Exporter installed and started"
else
    log "Node Exporter already installed"
fi

# ================================================================================
# SETUP LOG ROTATION
# ================================================================================

log "Configuring log rotation..."

cat > /etc/logrotate.d/glam <<'EOF'
/var/log/glam/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 640 deploy deploy
    sharedscripts
    postrotate
        docker-compose -f /opt/glam/docker-compose.prod.yaml kill -s USR1 nginx 2>/dev/null || true
    endscript
}

/opt/glam/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 640 deploy deploy
    sharedscripts
}

/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    copytruncate
}
EOF

log "Log rotation configured"

# ================================================================================
# INSTALL HELPER SCRIPTS
# ================================================================================

log "Installing helper scripts..."

# Docker cleanup script
cat > /usr/local/bin/docker-cleanup <<'EOF'
#!/bin/bash
echo "Cleaning up Docker resources..."
docker system prune -af --volumes
docker image prune -af
docker volume prune -f
journalctl --vacuum-time=7d
echo "Docker cleanup complete"
EOF
chmod +x /usr/local/bin/docker-cleanup

# System health check script
cat > /usr/local/bin/glam-health <<'EOF'
#!/bin/bash
echo "=== GLAM System Health Check ==="
echo ""
echo "System Resources:"
free -h
df -h /
echo ""
echo "Docker Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Size}}"
echo ""
echo "Service Health:"
for service in $(docker ps --format "{{.Names}}"); do
    if docker exec $service curl -sf http://localhost:8000/health &>/dev/null; then
        echo "✓ $service"
    else
        echo "✗ $service (unhealthy or no health endpoint)"
    fi
done
EOF
chmod +x /usr/local/bin/glam-health

# Add cron jobs
log "Setting up cron jobs..."
(crontab -l 2>/dev/null || true; echo "0 3 * * 0 /usr/local/bin/docker-cleanup") | crontab -
(crontab -l 2>/dev/null || true; echo "0 2 * * * cd /opt/glam && make db-backup 2>&1 | tee -a /var/log/glam/backup.log") | crontab -

# ================================================================================
# SSH HARDENING
# ================================================================================

log "Hardening SSH configuration..."

# Backup original SSH config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Apply secure SSH settings
sed -i 's/^#*PermitRootLogin .*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sed -i 's/^#*PubkeyAuthentication .*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication .*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#*PermitEmptyPasswords .*/PermitEmptyPasswords no/' /etc/ssh/sshd_config
sed -i 's/^#*X11Forwarding .*/X11Forwarding no/' /etc/ssh/sshd_config
sed -i 's/^#*MaxAuthTries .*/MaxAuthTries 3/' /etc/ssh/sshd_config

# Add additional security settings if not present
grep -q "^ClientAliveInterval" /etc/ssh/sshd_config || echo "ClientAliveInterval 300" >> /etc/ssh/sshd_config
grep -q "^ClientAliveCountMax" /etc/ssh/sshd_config || echo "ClientAliveCountMax 2" >> /etc/ssh/sshd_config

systemctl reload sshd
log "SSH hardening complete"

# ================================================================================
# CREATE ENVIRONMENT TEMPLATE
# ================================================================================

log "Creating environment template..."

cat > /opt/glam/.env.template <<'EOF'
# GLAM You Up Production Environment
# Copy to .env and update with your values

APP_ENV=production
DOMAIN=yourdomain.com
ACME_EMAIL=admin@yourdomain.com

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME_$(openssl rand -hex 16)

# Security
CLIENT_JWT_SECRET=$(openssl rand -base64 32)
INTERNAL_JWT_SECRET=$(openssl rand -base64 32)

# Add other required variables as needed
EOF

chown deploy:deploy /opt/glam/.env.template
log "Environment template created at /opt/glam/.env.template"

# ================================================================================
# FINAL SYSTEM INFORMATION
# ================================================================================

# Get system information
PUBLIC_IP=$(curl -s ifconfig.me)
PRIVATE_IP=$(hostname -I | awk '{print $1}')
MEMORY=$(free -h | grep Mem | awk '{print $2}')
DISK=$(df -h / | tail -1 | awk '{print $2}')
DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | sed 's/,$//')
COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4 | sed 's/,$//')

clear

echo ""
echo "=================================================================================="
echo "                    ✅ GLAM You Up Server Setup Complete!"
echo "=================================================================================="
echo ""
echo "📊 System Information:"
echo "  • Public IP:      $PUBLIC_IP"
echo "  • Private IP:     $PRIVATE_IP"
echo "  • Memory:         $MEMORY"
echo "  • Disk:           $DISK"
echo "  • Docker:         $DOCKER_VERSION"
echo "  • Compose:        $COMPOSE_VERSION"
echo ""
echo "🔒 Security:"
echo "  ✓ UFW Firewall enabled (22, 80, 443)"
echo "  ✓ Fail2ban configured and active"
echo "  ✓ Automatic security updates enabled"
echo "  ✓ SSH hardened"
echo "  ✓ Kernel parameters optimized"
echo ""
echo "👤 Users:"
echo "  ✓ Deploy user created with Docker access"
echo "  ✓ Root login restricted to SSH key only"
echo ""
echo "📁 Directories:"
echo "  ✓ Application:    /opt/glam"
echo "  ✓ Backups:        /var/backups/glam"
echo "  ✓ Logs:           /var/log/glam"
echo ""
echo "🔧 Monitoring:"
echo "  ✓ Node Exporter:  http://$PRIVATE_IP:9100/metrics"
echo "  ✓ Health Check:   Run 'glam-health' command"
echo ""
echo "=================================================================================="
echo "                              📝 NEXT STEPS"
echo "=================================================================================="
echo ""
echo "1️⃣  Add your SSH key to deploy user:"
echo "    ssh-copy-id deploy@$PUBLIC_IP"
echo ""
echo "2️⃣  Upload application code:"
echo "    scp -r . deploy@$PUBLIC_IP:/opt/glam/"
echo ""
echo "3️⃣  Configure environment:"
echo "    ssh deploy@$PUBLIC_IP"
echo "    cd /opt/glam"
echo "    cp .env.template .env"
echo "    nano .env  # Add your configuration"
echo ""
echo "4️⃣  Setup SSL certificate:"
echo "    sudo certbot certonly --standalone -d yourdomain.com"
echo ""
echo "5️⃣  Deploy application:"
echo "    cd /opt/glam"
echo "    make deploy-prod"
echo ""
echo "=================================================================================="
echo "                              ⚠️  IMPORTANT"
echo "=================================================================================="
echo ""
echo "• Change all default passwords immediately"
echo "• Configure DNS to point to: $PUBLIC_IP"
echo "• Setup backup strategy (database & files)"
echo "• Consider disabling password authentication after SSH key is added"
echo "• Monitor disk space regularly"
echo "• Review and adjust firewall rules as needed"
echo ""
echo "💡 Tip: Save this output for future reference!"
echo ""
echo "=================================================================================="