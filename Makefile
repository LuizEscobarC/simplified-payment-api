# Makefile for infra docker - payment api
.PHONY: help setup start start-monitoring hooks status stop clean all test lint pint

# Colors for output
GREEN := \033[0;32m
BLUE := \033[0;34m
YELLOW := \033[1;33m
NC := \033[0m # No Color

# Directories
INFRA_DIR := ./infra
DOCKER_DIR := ./docker

help: ## Show help
	@echo "$(BLUE)🚀 Infra Docker - Payment API$(NC)"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick start: $(GREEN)make all$(NC)"
	
setup: ## Prepare Python environment (venv + dependencies)
	@echo "$(BLUE)📦 Preparing Python environment...$(NC)"
	@cd $(INFRA_DIR) && \
	if [ ! -d ".venv" ]; then \
		echo "🐍 Creating virtual environment..."; \
		python3 -m venv .venv; \
	fi && \
	echo "🔧 Activating venv and installing dependencies..."; \
	bash -c "source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
	@echo "$(GREEN)✅ Python environment ready!$(NC)"

start: ## Start basic services using orchestrator
	@echo "$(BLUE)🚀 Starting basic services using orchestrator...$(NC)"
	@cd $(INFRA_DIR) && bash -c "source .venv/bin/activate && python3 $(DOCKER_DIR)/orchestrator.py start"

start-force: ## Start services ignoring partial failures
	@echo "$(BLUE)🚀 Starting services (ignoring partial failures)...$(NC)"
	@cd $(INFRA_DIR) && bash -c "source .venv/bin/activate && python3 $(DOCKER_DIR)/orchestrator.py start" || echo "$(YELLOW)⚠️  Some services failed but continuing...$(NC)"

start-monitoring: ## Start services + monitoring
	@echo "$(BLUE)🚀 Starting services with monitoring...$(NC)"
	@cd $(INFRA_DIR) && bash -c "source .venv/bin/activate && python3 $(DOCKER_DIR)/orchestrator.py start --monitoring"

hooks: ## Configure Git hooks for quality (automatic setup)
	@echo "$(BLUE)🔧 Configuring Git hooks automatically...$(NC)"
	@cd $(INFRA_DIR) && bash -c "source .venv/bin/activate && python3 $(DOCKER_DIR)/orchestrator.py hooks"
	@echo "$(GREEN)✅ Git hooks configured!$(NC)"

status: ## Show services status
	@echo "$(BLUE)📊 Services status...$(NC)"
	@cd $(INFRA_DIR) && bash -c "source .venv/bin/activate && python3 $(DOCKER_DIR)/orchestrator.py status"

stop: ## Stop all services
	@echo "$(YELLOW)🛑 Stopping services...$(NC)"
	@cd $(INFRA_DIR) && bash -c "source .venv/bin/activate && python3 $(DOCKER_DIR)/orchestrator.py stop"

clean: ## Clean containers and volumes
	@echo "$(YELLOW)🧹 Cleaning containers...$(NC)"
	@cd $(INFRA_DIR) && bash -c "source .venv/bin/activate && python3 $(DOCKER_DIR)/orchestrator.py cleanup"

test: ## Run PHP tests
	@echo "$(BLUE)🧪 Running PHP tests...$(NC)"
	@docker exec -it payment-api sh -c "cd /var/www/html && ./vendor/bin/phpunit"

lint: ## Run PHP linters (Pint, PHPMD, and PHPStan)
	@echo "$(BLUE)🔍 Running PHP linters...$(NC)"
	@docker exec -it payment-api sh -c "cd /var/www/html && ./vendor/bin/pint --test" && \
	docker exec -it payment-api sh -c "cd /var/www/html && /usr/local/bin/phpmd app xml phpmd.xml" && \
	docker exec -it payment-api sh -c "cd /var/www/html && ./vendor/bin/phpstan analyse app --memory-limit=-1"

pint: ## Run Pint to fix PHP code style
	@echo "$(BLUE)🎨 Running Pint to fix code style...$(NC)"
	@docker exec -it payment-api sh -c "cd /var/www/html && ./vendor/bin/pint"

fix-permissions: ## Fix file permissions for host editing
	@echo "$(BLUE)🔧 Fixing file permissions for host editing...$(NC)"
	@docker exec -it payment-api chown -R 1000:1000 /var/www/html
	@echo "$(GREEN)✅ Permissions fixed!$(NC)"

all: ## Prepare everything and start (complete setup with orchestrator)
	@echo "$(BLUE)🚀 Starting complete infrastructure setup...$(NC)"
	@cd $(INFRA_DIR) && \
	if [ ! -d ".venv" ]; then \
		echo "🐍 Creating virtual environment..."; \
		python3 -m venv .venv; \
	fi && \
	echo "🔧 Activating venv and installing dependencies..."; \
	bash -c "source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt" && \
	echo "✅ Python environment ready!" && \
	echo "$(BLUE)� Stopping any existing services...$(NC)" && \
	bash -c "source .venv/bin/activate && python3 $(DOCKER_DIR)/orchestrator.py stop" || true && \
	echo "$(BLUE)�🚀 Starting services with orchestrator...$(NC)" && \
	bash -c "source .venv/bin/activate && python3 $(DOCKER_DIR)/orchestrator.py start" && \
	echo "$(BLUE)🔧 Configuring Git hooks...$(NC)" && \
	bash -c "source .venv/bin/activate && python3 $(DOCKER_DIR)/orchestrator.py hooks" && \
	echo "$(BLUE)🧪 Running tests to verify setup...$(NC)" && \
	(cd .. && $(MAKE) test) && \
	echo "$(GREEN)🎉 Setup completed successfully! All tests passed.$(NC)" && \
	echo "$(BLUE)💡 Access: http://localhost$(NC)" || (echo "$(YELLOW)⚠️  Setup completed with issues. Check services and tests.$(NC)" && exit 1)