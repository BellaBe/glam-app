
Deployment Sequence:

Setup Vultr VM:

bashssh root@your-vultr-ip
bash setup.sh

Upload application:

bashscp -r . deploy@your-vultr-ip:/opt/glam/

Configure environment:

bashcp .env.prod.template .env
nano .env  # Fill in all values
bash validate-env.sh

Setup SSL:

bashbash ssl-setup.sh yourdomain.com admin@yourdomain.com

Deploy:

bashmake deploy-prod
GitHub Secrets Required:

VULTR_HOST - Your server IP
VULTR_SSH_KEY - Deploy user's private SSH key
GITHUB_TOKEN - Already available

All files are production-ready and follow best practices for security, performance, and maintainability. The nginx configuration ensures only the Shopify BFF app is publicly accessible, while all other services remain internal.



========================================
Deployment Options for Glam App
========================================

📱 Option 1: Deploy from Laptop (deploy.sh)
Direct deployment from your laptop to Vultr server

Pros: Faster for development, no GitHub required, immediate deployment
Use when: Testing, development, urgent fixes

🤖 Option 2: GitHub Actions (.github/workflows/deploy.yml)
Automated CI/CD deployment via GitHub

Pros: Automated, tested, traceable, team-friendly
Use when: Production releases, team deployments

How to Deploy from Your Laptop:
1. Initial Setup:
bash# Set your server details
export REMOTE_HOST="your-vultr-ip"
export REMOTE_USER="deploy"

# Or edit deploy.sh directly and change these lines:
REMOTE_HOST=${REMOTE_HOST:-"your-vultr-ip"}  # Change this
REMOTE_USER=${REMOTE_USER:-"deploy"}
2. Prepare Environment:
bash# Create production environment file
cp .env.prod.template .env.prod
# Edit and fill in all values
nano .env.prod
3. Deploy Commands:
bash# Full deployment with build
./infrastructure/scripts/deploy.sh deploy

# Quick deploy (restart only, no build)
./infrastructure/scripts/deploy.sh quick

# Check status
./infrastructure/scripts/deploy.sh status

# View logs
./infrastructure/scripts/deploy.sh logs
./infrastructure/scripts/deploy.sh logs merchant-service

# Rollback if needed
./infrastructure/scripts/deploy.sh rollback
What deploy.sh Does:

Pre-checks: Validates environment, SSH connection
Sync files: Uses rsync to efficiently copy files
Build on server: Builds Docker images on Vultr (saves bandwidth)
Backup: Creates database backups before deployment
Deploy: Runs migrations, starts services
Health checks: Verifies all services are running

Benefits of Laptop Deployment:

No GitHub required - Deploy directly
Faster iteration - No CI/CD pipeline wait
Selective sync - Only changed files uploaded
Local control - See exactly what's happening
Immediate rollback - Quick recovery if issues

Typical Workflow:
bash# Development
make dev-up  # Local development

# When ready to deploy
./infrastructure/scripts/deploy.sh status  # Check current state
./infrastructure/scripts/deploy.sh deploy  # Deploy to production

# Monitor
./infrastructure/scripts/deploy.sh logs    # Watch logs
Both deployment methods work together - use laptop deployment for quick iterations and GitHub Actions for official releases!


========================================
Setup Instructions
========================================
 the complete setup.sh script for Vultr VM initialization. This production-ready script includes:
Key Features:
🔒 Security Hardening:

UFW firewall with ports 22, 80, 443
Fail2ban with rules for SSH and nginx
Automatic security updates
SSH hardening (no root password login)
Kernel security parameters

🐳 Docker Setup:

Docker CE installation
Docker Compose v2.24.0
Deploy user with Docker permissions

⚙️ System Optimization:

File limits increased
Network stack optimization
Memory management tuning
4GB swap file creation

📊 Monitoring & Maintenance:

Node Exporter for Prometheus
Log rotation for all services
Docker cleanup cron job
Health check script (glam-health command)
Automatic backups cron job

📁 Directory Structure:
/opt/glam/          - Application root
/var/backups/glam/  - Backup storage
/var/log/glam/      - Application logs
/var/www/certbot/   - SSL certificates
👤 User Management:

deploy user created with:

Docker access
Sudo for specific commands
SSH key authentication ready



Usage:

Run on fresh Vultr VM:

bashwget https://raw.githubusercontent.com/yourrepo/glam/main/infrastructure/scripts/setup.sh
sudo bash setup.sh

After completion, you'll see:


System information summary
Security status
Next steps instructions
All configured services

Post-Setup Tasks:

Add SSH key:

bashssh-copy-id deploy@YOUR_SERVER_IP

Upload code:

bashscp -r . deploy@YOUR_SERVER_IP:/opt/glam/

Configure & deploy:

bashssh deploy@YOUR_SERVER_IP
cd /opt/glam
cp .env.template .env
nano .env  # Configure
make deploy-prod
The script is idempotent (can be run multiple times safely) and includes comprehensive error handling and logging. It provides a complete production-ready environment for your GLAM You Up platform on Vultr.