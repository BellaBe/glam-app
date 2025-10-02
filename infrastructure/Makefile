REMOTE_HOST ?= your-oracle-ip
REMOTE_USER ?= deploy
REMOTE_DIR ?= /opt/glam

.PHONY: deploy build push status logs

# Build all Python services locally
build:
	@echo "Building Python services..."
	docker-compose -f docker-compose.prod.yaml build

# Push to registry (optional if using Docker Hub)
push:
	docker-compose -f docker-compose.prod.yaml push

# Deploy to Oracle
deploy: build
	@echo "Deploying to Oracle Cloud..."
	rsync -avz --delete \
		--exclude='.git/' \
		--exclude='__pycache__/' \
		--exclude='*.pyc' \
		--exclude='.pytest_cache/' \
		--exclude='venv/' \
		--exclude='.env' \
		./ $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)/

	scp .env.prod $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)/.env

	ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_DIR) && docker-compose -f docker-compose.prod.yaml up -d"

status:
	ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_DIR) && docker-compose ps"

logs:
	ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_DIR) && docker-compose logs -f"

# Database operations
db-migrate:
	ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_DIR) && docker-compose exec merchant-service prisma migrate deploy"

db-backup:
	ssh $(REMOTE_USER)@$(REMOTE_HOST) "docker exec glam_postgres pg_dumpall -U glam > /var/backups/glam/backup_$(date +%Y%m%d).sql"
