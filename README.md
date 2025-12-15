# Task OCR Processing System

A monorepo for processing photos of handwritten task notes and todo lists using OCR (dots.ocr). The system extracts structured task information including task name, description, assignee, due date, and priority.

## Architecture

This system consists of the following components:

- **Django API Service**: REST API for uploading images and retrieving results
- **Celery Worker Service**: Asynchronous OCR processing
- **PostgreSQL**: Database for storing jobs and extracted tasks
- **Redis**: Message broker for Celery
- **MinIO**: S3-compatible object storage for images
- **Flower**: Celery monitoring dashboard (optional)

## Project Structure

```
.
├── backend/                    # Django application
│   ├── config/                # Django project settings
│   │   ├── settings.py       # Main settings
│   │   ├── celery.py         # Celery configuration
│   │   ├── urls.py           # URL routing
│   │   └── wsgi.py           # WSGI application
│   ├── tasks/                 # Main Django app
│   │   ├── models.py         # Database models
│   │   ├── views.py          # API views
│   │   ├── serializers.py    # DRF serializers
│   │   ├── tasks.py          # Celery tasks
│   │   ├── ocr_service.py    # OCR processing service
│   │   └── urls.py           # App URL routing
│   ├── manage.py              # Django management script
│   └── requirements.txt       # Python dependencies
├── docker/                    # Docker configurations
│   ├── api/
│   │   └── Dockerfile        # API service Dockerfile
│   └── worker/
│       └── Dockerfile        # Worker service Dockerfile
├── docker-compose.yml         # Docker Compose configuration
├── .env.example              # Environment variables template
├── .gitignore
├── .dockerignore
└── README.md
```

## Prerequisites

- Docker and Docker Compose
- At least 4GB RAM available for Docker
- Internet connection for pulling Docker images

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Set Up Environment Variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` and update the values as needed (especially change secret keys and passwords for production).

### 3. Build and Start Services

Build and start all services using Docker Compose:

```bash
docker-compose up --build
```

This will start:
- API service on http://localhost:8000
- MinIO console on http://localhost:9001
- Flower (Celery monitoring) on http://localhost:5555
- PostgreSQL on localhost:5432
- Redis on localhost:6379

### 4. Run Database Migrations

In a new terminal, run migrations:

```bash
docker-compose exec api python manage.py migrate
```

### 5. Create Django Superuser (Optional)

To access the Django admin interface:

```bash
docker-compose exec api python manage.py createsuperuser
```

### 6. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

## API Usage

### Upload Image for Processing

Upload a handwritten task note image:

```bash
curl -X POST http://localhost:8000/api/upload/ \
  -F "image=@/path/to/your/image.jpg"
```

Response:
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Image uploaded successfully. Processing started."
}
```

### Check Processing Status

Poll for status using the transaction ID:

```bash
curl http://localhost:8000/api/status/<transaction_id>/
```

Response (while processing):
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "processing_duration": null,
  "task_count": 0,
  "error_message": null
}
```

Response (completed):
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "original_filename": "tasks.jpg",
  "image_size": 2048576,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:45Z",
  "started_at": "2024-01-15T10:30:02Z",
  "completed_at": "2024-01-15T10:30:45Z",
  "processing_duration": 43.5,
  "ocr_confidence": 0.87,
  "error_message": null,
  "extracted_tasks": [
    {
      "id": 1,
      "task_name": "Review project proposal",
      "description": "Review and provide feedback on Q1 project proposal document",
      "assignee": "John Doe",
      "due_date": "2024-01-18",
      "priority": "high",
      "position_index": 0,
      "confidence_score": 0.89,
      "bbox_x": 50,
      "bbox_y": 100,
      "bbox_width": 400,
      "bbox_height": 60,
      "created_at": "2024-01-15T10:30:45Z"
    }
  ]
}
```

### Get Full Job Details

Retrieve complete job information:

```bash
curl http://localhost:8000/api/jobs/<transaction_id>/
```

## OCR Integration

### Using dots.ocr

This project is designed to integrate with dots.ocr for handwritten text recognition. The current implementation includes a mock OCR service for testing.

To integrate actual dots.ocr:

1. Install the dots.ocr package:
   ```bash
   # Add to backend/requirements.txt
   # dotsocr==x.x.x  # Replace with actual package name and version
   ```

2. Update `backend/tasks/ocr_service.py`:
   - Replace the `_mock_extract_tasks` method with actual dots.ocr API calls
   - Implement the `_parse_ocr_results` method based on dots.ocr output format
   - Add API key configuration in settings

3. Add dots.ocr credentials to `.env`:
   ```
   DOTS_OCR_API_KEY=your-api-key-here
   ```

## Development

### Running Locally Without Docker

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Set up local PostgreSQL, Redis, and MinIO

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Run the development server:
   ```bash
   python manage.py runserver
   ```

6. Run Celery worker (in another terminal):
   ```bash
   celery -A config worker --loglevel=info
   ```

### Running Tests

```bash
docker-compose exec api python manage.py test
```

### Viewing Logs

View logs for specific services:

```bash
# API logs
docker-compose logs -f api

# Worker logs
docker-compose logs -f worker

# All logs
docker-compose logs -f
```

## Monitoring

### Flower Dashboard

Access the Celery monitoring dashboard at http://localhost:5555

### Django Admin

Access the Django admin interface at http://localhost:8000/admin

### MinIO Console

Access the MinIO console at http://localhost:9001

## Production Deployment

For production deployment:

1. Update `.env` with strong passwords and secret keys
2. Set `DJANGO_DEBUG=False`
3. Configure proper `ALLOWED_HOSTS`
4. Use a production-grade database (managed PostgreSQL)
5. Set up SSL/TLS certificates
6. Configure proper CORS settings
7. Use a reverse proxy (Nginx/Traefik)
8. Set up monitoring and logging
9. Configure backup strategies

## Troubleshooting

### Services not starting

Check Docker logs:
```bash
docker-compose logs
```

### Database connection errors

Ensure PostgreSQL is healthy:
```bash
docker-compose ps postgres
```

### Worker not processing tasks

Check Redis connection and worker logs:
```bash
docker-compose logs worker
docker-compose logs redis
```

### Image upload fails

Check MinIO is running and bucket is created:
```bash
docker-compose logs minio
docker-compose logs minio-init
```

## API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload/` | Upload image for OCR processing |
| GET | `/api/status/<transaction_id>/` | Check processing status |
| GET | `/api/jobs/<transaction_id>/` | Get full job details |

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DJANGO_SECRET_KEY`: Django secret key (change in production)
- `POSTGRES_*`: Database credentials
- `REDIS_URL`: Redis connection URL
- `MINIO_*`: MinIO/S3 configuration
- `OCR_CONFIDENCE_THRESHOLD`: Minimum OCR confidence score

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Support

For issues and questions, please [create an issue](link-to-issues) or contact [your-contact-info].
