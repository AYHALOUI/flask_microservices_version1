# Makefile for the microservices project

.PHONY: help build up down logs clean test restart status ps

# Default target
help:
	@echo "Available commands:"
	@echo "  make build        - Build all services"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - Show logs from all services"
	@echo "  make logs-service - Show logs from a specific service (e.g., make logs-gateway)"
	@echo "  make ps           - List running services"
	@echo "  make status       - Check health of all services"
	@echo "  make clean        - Remove containers, networks, and volumes"
	@echo "  make test         - Run connectivity tests"
	@echo "  make rebuild      - Rebuild and restart a specific service (e.g., make rebuild SERVICE=gateway)"

# Build all services
build:
	docker-compose build

# Start all services
up:
	docker-compose up
	@echo "Services are starting..."
	@echo "Check status with: make ps"
	@echo "Access the gateway at: http://localhost:9000"

# Stop all services
down:
	docker-compose down
	@echo "All services have been stopped"

# Restart all services
restart:
	docker-compose restart
	@echo "All services have been restarted"

# Display logs for all services
logs:
	docker-compose logs -f

# Display logs for a specific service
logs-%:
	docker-compose logs -f $*

# Display running services
ps:
	docker-compose ps

# Clean up resources
clean:
	docker-compose down -v --remove-orphans
	@echo "Cleaned up containers, networks, and volumes"

# Run connectivity tests
test:
	@echo "Checking gateway health..."
	curl -s http://localhost:9000/health | jq

# Check health status of all services
status:
	@echo "Checking service health status..."
	@for service in gateway service_contacts service_transform service_connectivity service_storage service_debugger service_project; do \
		echo -n "$$service: "; \
		STATUS=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/api/$${service#service_}/health); \
		if [ "$$STATUS" = "200" ]; then \
			echo "OK (200)"; \
		else \
			echo "NOT OK ($$STATUS)"; \
		fi; \
	done

# Rebuild and restart a specific service
rebuild:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Please specify a service: make rebuild SERVICE=gateway"; \
		exit 1; \
	fi
	docker-compose build $(SERVICE)
	docker-compose stop $(SERVICE)
	docker-compose rm -f $(SERVICE)
	docker-compose up -d $(SERVICE)
	@echo "Service $(SERVICE) has been rebuilt and restarted"

# Initialize directories (if needed)
init:
	mkdir -p data/gateway data/contacts data/connectivity data/storage data/debugger data/project
	@echo "Data directories created"