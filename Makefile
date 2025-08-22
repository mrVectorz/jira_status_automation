# Makefile for JIRA Status Automation Container
# Provides convenient commands for container management

.PHONY: help build setup start stop restart status logs generate shell clean

# Default target
help: ## Show this help message
	@echo "JIRA Status Automation - Container Management"
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Environment Variables:"
	@echo "  WEB_PORT   - Port inside container that web server listens on (default: 8080)"
	@echo "  HOST_PORT  - Port on host machine to map to container (default: 8080)"
	@echo "  TZ         - Timezone (default: UTC)"
	@echo ""
	@echo "Examples:"
	@echo "  make start                              # Start with default settings"
	@echo "  HOST_PORT=9090 make start               # Start on host port 9090"
	@echo "  WEB_PORT=3000 HOST_PORT=9090 make start # Container port 3000, host port 9090"
	@echo "  make logs                               # View logs"
	@echo "  make generate                           # Generate report manually"

build: ## Build the container image (OCI format)
	@./run-podman.sh build

build-docker: ## Build with Docker format (includes HEALTHCHECK)
	@./run-podman.sh build-docker

setup: ## Set up directories and configuration
	@./run-podman.sh setup

start: ## Set up, build and start the container
	@./run-podman.sh start

stop: ## Stop and remove the container
	@./run-podman.sh stop

restart: ## Stop, rebuild and start the container
	@./run-podman.sh restart

status: ## Show container status
	@./run-podman.sh status

logs: ## Show container logs (real-time)
	@./run-podman.sh logs

generate: ## Generate a report manually
	@./run-podman.sh generate

shell: ## Open a shell in the running container
	@./run-podman.sh shell

health: ## Run health check
	@./run-podman.sh health

clean: ## Stop container and remove image
	@./run-podman.sh stop
	@echo "Force removing container (if exists)..."
	@podman rm -f jira-status-automation 2>/dev/null || echo "Container not found"
	@echo "Removing container image..."
	@podman rmi jira-status-automation 2>/dev/null || echo "Image not found"
	@echo "Cleanup completed"

# Docker Compose alternatives
compose-up: ## Start using docker-compose/podman-compose
	@if command -v podman-compose >/dev/null 2>&1; then \
		podman-compose up -d; \
	elif command -v docker-compose >/dev/null 2>&1; then \
		docker-compose up -d; \
	else \
		echo "Neither podman-compose nor docker-compose found"; \
		exit 1; \
	fi

compose-down: ## Stop using docker-compose/podman-compose
	@if command -v podman-compose >/dev/null 2>&1; then \
		podman-compose down; \
	elif command -v docker-compose >/dev/null 2>&1; then \
		docker-compose down; \
	else \
		echo "Neither podman-compose nor docker-compose found"; \
		exit 1; \
	fi

compose-logs: ## Show logs using docker-compose/podman-compose
	@if command -v podman-compose >/dev/null 2>&1; then \
		podman-compose logs -f; \
	elif command -v docker-compose >/dev/null 2>&1; then \
		docker-compose logs -f; \
	else \
		echo "Neither podman-compose nor docker-compose found"; \
		exit 1; \
	fi
