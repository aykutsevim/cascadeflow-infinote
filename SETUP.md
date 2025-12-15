# Quick Setup Guide

## Prerequisites

- Docker Desktop installed and running
- Git installed
- 4GB+ RAM available for Docker

## Quick Start (5 minutes)

### 1. Clone and Setup Environment

```bash
# Navigate to project directory
cd infinote

# Copy environment file
cp .env.example .env

# (Optional) Edit .env if you want to customize settings
# For development, the defaults work fine
```

### 2. Start the System

```bash
# Build and start all services
docker-compose up --build -d

# Wait for services to start (about 30-60 seconds)
# You can watch the logs with:
docker-compose logs -f
```

### 3. Initialize Database

```bash
# Run database migrations
docker-compose exec api python manage.py migrate

# Create an admin user (optional)
docker-compose exec api python manage.py createsuperuser
```

### 4. Verify Installation

Visit these URLs to confirm everything is working:

- API: http://localhost:8000/api/
- Django Admin: http://localhost:8000/admin (use superuser credentials)
- MinIO Console: http://localhost:9001 (login: minioadmin / minioadmin123)
- Flower (Celery Monitor): http://localhost:5555

## Testing the API

### Upload a test image:

```bash
# Using curl (replace with your actual image path)
curl -X POST http://localhost:8000/api/upload/ \
  -F "image=@/path/to/test-image.jpg"
```

You'll get a response like:
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Image uploaded successfully. Processing started."
}
```

### Check processing status:

```bash
# Replace <transaction_id> with the ID from previous response
curl http://localhost:8000/api/status/<transaction_id>/
```

## Using Makefile (Alternative)

If you have `make` installed, you can use convenient shortcuts:

```bash
# Start everything
make dev-setup

# View logs
make logs

# Create superuser
make createsuperuser

# Run tests
make test

# Stop everything
make down

# See all commands
make help
```

## Common Issues

### Port already in use

If you see "port already allocated" errors:

1. Check what's using the ports:
   ```bash
   # On Windows (PowerShell)
   netstat -ano | findstr ":8000"

   # On Linux/Mac
   lsof -i :8000
   ```

2. Either stop the conflicting service or change the port in `.env`:
   ```
   API_PORT=8001
   ```

### Services not starting

1. Check Docker is running
2. Check logs for specific service:
   ```bash
   docker-compose logs api
   docker-compose logs worker
   docker-compose logs postgres
   ```

### Database connection refused

Wait a bit longer for PostgreSQL to initialize (first run takes longer), then retry:
```bash
docker-compose restart api
```

## Stopping the System

```bash
# Stop services but keep data
docker-compose down

# Stop services and remove all data (fresh start)
docker-compose down -v
```

## Next Steps

1. Read the main [README.md](README.md) for detailed documentation
2. Check the API documentation
3. Integrate with actual dots.ocr (see README.md)
4. Customize the OCR processing logic in `backend/tasks/ocr_service.py`

## Development Workflow

```bash
# Start services
docker-compose up -d

# Make code changes in backend/
# Changes are automatically reflected (volume mounted)

# View logs to debug
docker-compose logs -f api

# Restart specific service after config changes
docker-compose restart api

# Stop services when done
docker-compose down
```

## Useful Commands

```bash
# Access Django shell
docker-compose exec api python manage.py shell

# Access database shell
docker-compose exec postgres psql -U taskocr_user -d taskocr

# Access API container bash
docker-compose exec api bash

# View all running containers
docker-compose ps

# Check service health
docker-compose exec api python manage.py check

# Run Django management commands
docker-compose exec api python manage.py <command>
```

## File Structure Quick Reference

```
infinote/
├── backend/               # Django application code
│   ├── config/           # Settings and configuration
│   ├── tasks/            # Main app (models, views, tasks)
│   └── manage.py
├── docker/               # Dockerfiles
│   ├── api/Dockerfile
│   └── worker/Dockerfile
├── docker-compose.yml    # Service orchestration
└── .env                  # Configuration (create from .env.example)
```

## Support

If you encounter issues not covered here, check:
- Docker logs: `docker-compose logs`
- Django logs in the API container
- Worker logs: `docker-compose logs worker`
- Database connectivity: `docker-compose exec postgres pg_isready`
