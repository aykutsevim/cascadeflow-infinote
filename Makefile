# Makefile for Task OCR Processing System

.PHONY: help build up down restart logs shell migrate createsuperuser test clean

help:
	@echo "Available commands:"
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-api       - View API service logs"
	@echo "  make logs-worker    - View worker service logs"
	@echo "  make shell          - Open Django shell"
	@echo "  make bash           - Open bash in API container"
	@echo "  make migrate        - Run database migrations"
	@echo "  make makemigrations - Create new migrations"
	@echo "  make createsuperuser - Create Django superuser"
	@echo "  make test           - Run tests"
	@echo "  make clean          - Remove containers and volumes"
	@echo "  make ps             - Show running containers"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services are starting..."
	@echo "API: http://localhost:8000"
	@echo "MinIO Console: http://localhost:9001"
	@echo "Flower: http://localhost:5555"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-worker:
	docker-compose logs -f worker

shell:
	docker-compose exec api python manage.py shell

bash:
	docker-compose exec api bash

migrate:
	docker-compose exec api python manage.py migrate

makemigrations:
	docker-compose exec api python manage.py makemigrations

createsuperuser:
	docker-compose exec api python manage.py createsuperuser

test:
	docker-compose exec api python manage.py test

ps:
	docker-compose ps

clean:
	docker-compose down -v
	@echo "Containers and volumes removed"

# Development commands
dev-setup: build up migrate
	@echo "Development environment ready!"
	@echo "Run 'make createsuperuser' to create an admin user"

# Quick start
start: up

stop: down
