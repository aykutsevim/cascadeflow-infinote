# Project Structure Reference

## Complete Directory Tree

```
infinote/
│
├── backend/                          # Django Application
│   ├── config/                      # Django Project Configuration
│   │   ├── __init__.py             # Makes config a package, imports celery
│   │   ├── settings.py             # Main Django settings
│   │   ├── celery.py               # Celery configuration
│   │   ├── urls.py                 # URL routing
│   │   ├── wsgi.py                 # WSGI application
│   │   └── asgi.py                 # ASGI application (for async)
│   │
│   ├── tasks/                       # Main Django App
│   │   ├── migrations/             # Database migrations
│   │   │   └── __init__.py
│   │   ├── __init__.py             # App initialization
│   │   ├── apps.py                 # App configuration
│   │   ├── models.py               # Database models (ProcessingJob, ExtractedTask)
│   │   ├── views.py                # API views (upload, status, job detail)
│   │   ├── serializers.py          # DRF serializers
│   │   ├── urls.py                 # App URL routing
│   │   ├── admin.py                # Django admin configuration
│   │   ├── tasks.py                # Celery tasks (OCR processing)
│   │   ├── ocr_service.py          # OCR service integration
│   │   └── tests.py                # Unit tests
│   │
│   ├── manage.py                    # Django management script
│   └── requirements.txt             # Python dependencies
│
├── docker/                          # Docker Configurations
│   ├── api/
│   │   └── Dockerfile              # Dockerfile for API service
│   └── worker/
│       └── Dockerfile              # Dockerfile for Worker service
│
├── docker-compose.yml               # Main Docker Compose configuration
├── docker-compose.dev.yml           # Development overrides
│
├── .env.example                     # Environment variables template
├── .env                            # Actual environment variables (git-ignored)
│
├── .gitignore                       # Git ignore rules
├── .dockerignore                    # Docker ignore rules
│
├── Makefile                         # Convenience commands
│
├── README.md                        # Main documentation
├── SETUP.md                         # Quick setup guide
├── API_EXAMPLES.md                  # API usage examples
└── PROJECT_STRUCTURE.md             # This file
```

## Component Breakdown

### Backend Application (`backend/`)

The Django application that powers the API and contains all business logic.

**Key Files:**
- `config/settings.py` - All Django and service configurations
- `config/celery.py` - Celery worker setup
- `tasks/models.py` - Database schema
- `tasks/views.py` - API endpoints
- `tasks/tasks.py` - Async OCR processing
- `tasks/ocr_service.py` - OCR integration (customize for dots.ocr)

### Docker Configuration (`docker/`)

Separate Dockerfiles for each service component.

**Services:**
- `api/Dockerfile` - Django API server with Gunicorn
- `worker/Dockerfile` - Celery worker for background processing

### Infrastructure (`docker-compose.yml`)

Orchestrates all services:
- **api** - Django REST API (port 8000)
- **worker** - Celery worker
- **postgres** - PostgreSQL database (port 5432)
- **redis** - Message broker (port 6379)
- **minio** - S3-compatible storage (ports 9000, 9001)
- **beat** - Celery scheduler (optional)
- **flower** - Celery monitoring (port 5555)

## Data Flow

```
1. Client uploads image
   ↓
2. API saves to MinIO
   ↓
3. ProcessingJob created in PostgreSQL
   ↓
4. Celery task queued in Redis
   ↓
5. Worker picks up task
   ↓
6. OCR processing (dots.ocr)
   ↓
7. ExtractedTasks saved to PostgreSQL
   ↓
8. ProcessingJob marked as completed
   ↓
9. Client polls status endpoint
   ↓
10. API returns extracted tasks
```

## Database Schema

### ProcessingJob Table
```
- id (Primary Key)
- transaction_id (UUID, indexed)
- image_path (String)
- original_filename (String)
- image_size (Integer)
- status (Enum: pending/processing/completed/failed)
- celery_task_id (String)
- error_message (Text)
- error_traceback (Text)
- created_at (DateTime)
- updated_at (DateTime)
- started_at (DateTime)
- completed_at (DateTime)
- processing_duration (Float)
- ocr_confidence (Float)
```

### ExtractedTask Table
```
- id (Primary Key)
- job_id (Foreign Key → ProcessingJob)
- task_name (String)
- description (Text)
- assignee (String)
- due_date (Date)
- priority (Enum: low/medium/high/urgent)
- position_index (Integer)
- confidence_score (Float)
- bbox_x, bbox_y, bbox_width, bbox_height (Integer)
- created_at (DateTime)
- updated_at (DateTime)
```

## API Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| POST | `/api/upload/` | Upload image | `multipart/form-data` | Transaction ID |
| GET | `/api/status/{id}/` | Check status | - | Status + tasks (if done) |
| GET | `/api/jobs/{id}/` | Get full details | - | Complete job info |

## Environment Variables

Key variables in `.env`:

**Django:**
- `DJANGO_SECRET_KEY` - Secret key for Django
- `DJANGO_DEBUG` - Debug mode (True/False)
- `DJANGO_ALLOWED_HOSTS` - Allowed hosts

**Database:**
- `POSTGRES_DB` - Database name
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_HOST` - Database host
- `POSTGRES_PORT` - Database port

**Redis:**
- `REDIS_URL` - Redis connection URL
- `CELERY_BROKER_URL` - Celery broker
- `CELERY_RESULT_BACKEND` - Celery results

**MinIO/S3:**
- `MINIO_ENDPOINT` - MinIO server endpoint
- `MINIO_ACCESS_KEY` - Access key
- `MINIO_SECRET_KEY` - Secret key
- `MINIO_BUCKET` - Bucket name
- `MINIO_USE_SSL` - Use SSL (True/False)

**OCR:**
- `OCR_CONFIDENCE_THRESHOLD` - Minimum confidence (0.0-1.0)

## Key Technologies

- **Django 4.2** - Web framework
- **Django REST Framework** - API framework
- **Celery 5.3** - Task queue
- **PostgreSQL 15** - Database
- **Redis 7** - Message broker
- **MinIO** - Object storage
- **Gunicorn** - WSGI server
- **Docker & Docker Compose** - Containerization

## Customization Points

### 1. OCR Integration (`backend/tasks/ocr_service.py`)

Replace the mock implementation with actual dots.ocr:

```python
def extract_tasks(self, image: Image.Image):
    # Replace mock with:
    # result = self.ocr_client.process_image(image)
    # tasks = self._parse_ocr_results(result)
    # return {'tasks': tasks, 'raw_result': result}
    pass
```

### 2. Task Parsing (`backend/tasks/ocr_service.py`)

Implement parsing logic based on dots.ocr output format:

```python
def _parse_ocr_results(self, ocr_result):
    # Parse OCR results into structured task data
    # Extract: name, description, assignee, due_date, priority
    pass
```

### 3. Authentication (`backend/config/settings.py`)

Add authentication to REST_FRAMEWORK settings:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### 4. File Storage

Currently uses MinIO. Can switch to AWS S3, Google Cloud Storage, etc. by changing `STORAGES` in settings.

### 5. Database

Currently uses PostgreSQL. Can switch to MongoDB by:
1. Using `djongo` adapter
2. Updating `DATABASES` configuration
3. Adjusting models for NoSQL

## Development Workflow

1. Make code changes in `backend/`
2. Changes auto-reload (volume mounted)
3. View logs: `docker-compose logs -f api`
4. Run tests: `docker-compose exec api python manage.py test`
5. Access Django shell: `docker-compose exec api python manage.py shell`
6. Create migrations: `docker-compose exec api python manage.py makemigrations`
7. Apply migrations: `docker-compose exec api python manage.py migrate`

## Production Checklist

- [ ] Change `DJANGO_SECRET_KEY`
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use strong database passwords
- [ ] Enable SSL/HTTPS
- [ ] Set up domain and DNS
- [ ] Configure CORS properly
- [ ] Implement authentication
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Configure backups
- [ ] Set up CI/CD
- [ ] Use managed services (RDS, ElastiCache)
- [ ] Implement rate limiting
- [ ] Add logging and alerting
- [ ] Security audit
- [ ] Load testing

## Useful Commands

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec api python manage.py migrate

# Create superuser
docker-compose exec api python manage.py createsuperuser

# Access Django shell
docker-compose exec api python manage.py shell

# Run tests
docker-compose exec api python manage.py test

# Access database
docker-compose exec postgres psql -U taskocr_user -d taskocr

# Stop everything
docker-compose down

# Clean everything (including volumes)
docker-compose down -v

# Rebuild
docker-compose up --build
```

## Monitoring URLs

- API: http://localhost:8000
- Django Admin: http://localhost:8000/admin
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)
- Flower: http://localhost:5555
- pgAdmin: http://localhost:5050 (if using dev compose)

## File Sizes

- Total project: ~50 KB (code only)
- Docker images: ~1.5 GB (all services)
- Database: Depends on usage
- Storage: Depends on uploaded images

## Next Steps

1. Integrate with actual dots.ocr
2. Implement authentication
3. Add frontend application
4. Set up CI/CD pipeline
5. Deploy to production
6. Add monitoring and alerting
7. Implement rate limiting
8. Add webhooks for notifications
9. Create user documentation
10. Performance optimization
