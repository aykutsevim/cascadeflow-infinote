# Infinote - Handwritten Task OCR API

A powerful OCR (Optical Character Recognition) system for extracting tasks from handwritten notes using the dots.ocr vision-language model.

## Features

- **Intelligent Task Extraction**: Uses dots.ocr AI model to extract tasks from handwritten images
- **Smart Assignee Detection**: Automatically identifies and separates assignee names from task descriptions
- **Date Recognition**: Extracts and parses due dates in multiple formats
- **Priority Detection**: Identifies task priority based on visual cues
- **High Performance**: Model loaded once and reused across requests (no memory leaks)
- **Async Processing**: Background task processing with Celery
- **Scalable Architecture**: Docker-based deployment with GPU support

## API Documentation

### Base URL
```
http://localhost:8000/api
```

### Endpoints

#### 1. Upload Image for OCR Processing

**POST** `/api/upload/`

Upload a handwritten task list image for processing.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form data with `image` field

**Example:**
```bash
curl -X POST -F "image=@tasks_photo.jpg" http://localhost:8000/api/upload/
```

**Response:**
```json
{
  "transaction_id": "b0f28f47-931b-476a-aa86-5159482bc777",
  "status": "pending",
  "message": "Image uploaded successfully. Processing started."
}
```

#### 2. Check Processing Status

**GET** `/api/status/{transaction_id}/`

Check the processing status and get results when completed.

**Example:**
```bash
curl http://localhost:8000/api/status/b0f28f47-931b-476a-aa86-5159482bc777/
```

**Response (Completed):**
```json
{
  "transaction_id": "b0f28f47-931b-476a-aa86-5159482bc777",
  "status": "completed",
  "original_filename": "tasks_photo.jpg",
  "image_size": 1598098,
  "created_at": "2025-12-15T19:59:16.874215Z",
  "updated_at": "2025-12-15T20:00:29.273155Z",
  "started_at": "2025-12-15T19:59:16.904698Z",
  "completed_at": "2025-12-15T20:00:29.273102Z",
  "processing_duration": 72.368404,
  "ocr_confidence": 0.9,
  "error_message": null,
  "extracted_tasks": [
    {
      "id": 36,
      "task_name": "Write requirements",
      "description": "",
      "assignee": "Aykut",
      "due_date": null,
      "priority": "medium",
      "position_index": 0,
      "confidence_score": 0.9,
      "bbox_x": 37,
      "bbox_y": 324,
      "bbox_width": 269,
      "bbox_height": 31,
      "created_at": "2025-12-15T20:00:29.257273Z"
    }
  ]
}
```

## Input Format

### Supported Image Formats
- **File Types**: JPG, JPEG, PNG
- **Max Size**: Recommended < 5MB
- **Resolution**: Automatically resized if > 1024px on longest side
- **Content**: Handwritten task lists

### Handwriting Format Examples

The OCR system intelligently extracts tasks with assignees and dates in various formats:

#### Format 1: Arrow Notation
```
- Write requirements → Aykut
- Get approval → Hasan 17/12/2025
- Convert to Farsi → Hasan
```

**Extracted:**
- Task: "Write requirements", Assignee: "Aykut"
- Task: "Get approval", Assignee: "Hasan", Due Date: "2025-12-17"
- Task: "Convert to Farsi", Assignee: "Hasan"

#### Format 2: Parentheses
```
- Review code (Sarah)
- Update docs (John Smith)
```

**Extracted:**
- Task: "Review code", Assignee: "Sarah"
- Task: "Update docs", Assignee: "John Smith"

#### Format 3: Explicit Assignment
```
- Deploy to production assigned to: DevOps Team
- Fix bug owner: Mike
```

**Extracted:**
- Task: "Deploy to production", Assignee: "DevOps Team"
- Task: "Fix bug", Assignee: "Mike"

#### Format 4: @ Mentions
```
- Schedule meeting @alice
- Send report @bob
```

**Extracted:**
- Task: "Schedule meeting", Assignee: "alice"
- Task: "Send report", Assignee: "bob"

#### Format 5: Brackets
```
- Design mockups [Emma]
- Write tests [Tom]
```

**Extracted:**
- Task: "Design mockups", Assignee: "Emma"
- Task: "Write tests", Assignee: "Tom"

## Output Format

### Extracted Task Object

Each extracted task contains the following fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | integer | Unique database ID | `36` |
| `task_name` | string | The main action item (cleaned, without assignee or date) | `"Write requirements"` |
| `description` | string | Additional task details if any | `""` |
| `assignee` | string/null | Person responsible for the task | `"Aykut"` |
| `due_date` | date/null | Deadline in YYYY-MM-DD format | `"2025-12-17"` |
| `priority` | string | Task priority: `"low"`, `"medium"`, `"high"`, `"urgent"` | `"medium"` |
| `position_index` | integer | Order of task in the original list (0-based) | `0` |
| `confidence_score` | float | OCR confidence (0.0 - 1.0) | `0.9` |
| `bbox_x` | integer | X coordinate of task bounding box | `37` |
| `bbox_y` | integer | Y coordinate of task bounding box | `324` |
| `bbox_width` | integer | Width of task bounding box | `269` |
| `bbox_height` | integer | Height of task bounding box | `31` |
| `created_at` | datetime | When the task was extracted | `"2025-12-15T20:00:29.257273Z"` |

### Processing Status Values

| Status | Description |
|--------|-------------|
| `pending` | Task queued for processing |
| `processing` | OCR in progress |
| `completed` | Processing finished successfully |
| `failed` | Processing encountered an error |

## How It Works

### 1. Intelligent Extraction Process

The system uses advanced pattern recognition to intelligently extract and separate task components:

```
Input:  "Write requirements → Aykut 15/12/2025"

Parsing:
1. Detect arrow pattern: "→ Aykut"
2. Extract assignee: "Aykut"
3. Detect date pattern: "15/12/2025"
4. Extract date: "2025-12-15"
5. Clean task name: "Write requirements"

Output:
- task_name: "Write requirements"
- assignee: "Aykut"
- due_date: "2025-12-15"
```

### 2. Priority Detection

Priority is automatically detected based on visual cues:

| Visual Cue | Priority |
|------------|----------|
| "!!!", "urgent", "ASAP", "critical" | `urgent` |
| "!!", "high", "important" | `high` |
| "!", "low", "minor", "whenever" | `low` |
| Default (no markers) | `medium` |

### 3. Date Format Support

The system recognizes multiple date formats:

| Format | Example | Parsed As |
|--------|---------|-----------|
| DD/MM/YYYY | 17/12/2025 | 2025-12-17 |
| MM/DD/YYYY | 12/17/2025 | 2025-12-17 |
| YYYY-MM-DD | 2025-12-17 | 2025-12-17 |
| Month Day | Dec 17 | 2025-12-17 |

## Architecture

### Technology Stack

- **Backend**: Django + Django REST Framework
- **OCR Engine**: dots.ocr (Vision-Language Model)
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL
- **Storage**: MinIO (S3-compatible)
- **Deployment**: Docker + Docker Compose
- **GPU Support**: NVIDIA CUDA (optional)

### Model Performance

- **First Request**: ~65-72 seconds (includes model loading)
- **Subsequent Requests**: ~6-8 seconds (model cached in memory)
- **Memory**: Stable across requests (no memory leaks)
- **GPU VRAM**: ~6-8GB (model loaded once)

### Singleton Pattern

The OCR model uses a singleton pattern to ensure:
- ✅ Model loaded only **once** on first request
- ✅ Reused across all subsequent requests
- ✅ No memory leaks or VRAM accumulation
- ✅ Fast inference after initial load

## Installation

### Prerequisites

- Docker & Docker Compose
- NVIDIA GPU (optional, for faster processing)
- NVIDIA Docker Runtime (for GPU support)

### Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd infinote
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Download dots.ocr model:
```bash
python backend/tools/download_dots_model.py
```

4. Start services (CPU):
```bash
docker-compose up -d
```

Or with GPU support:
```bash
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

5. Test the API:
```bash
python test_simple.py
```

## Testing

### Simple Test Script

```python
import requests
import time

# Upload image
with open('test_assets/tasks_photo.jpg', 'rb') as f:
    response = requests.post('http://localhost:8000/api/upload/', files={'image': f})
    transaction_id = response.json()['transaction_id']

# Wait for processing
time.sleep(10)

# Get results
response = requests.get(f'http://localhost:8000/api/status/{transaction_id}/')
print(response.json())
```

### Test Files Included

- `test_simple.py` - Basic upload and status check
- `test_upload_twice.py` - Verify model reuse and performance
- `test_assets/tasks_photo.jpg` - Sample handwritten task list

## Performance Optimization

### First Call (with model loading)
```
Total Time: 65-72 seconds
├─ Model Loading: ~60 seconds
└─ Inference: ~6-8 seconds
```

### Subsequent Calls (model cached)
```
Total Time: 6-8 seconds
├─ Model Loading: 0 seconds (cached)
└─ Inference: ~6-8 seconds
```

**Speedup**: 87-92% faster after first call

## Example Use Cases

1. **Project Management**: Convert handwritten meeting notes into structured tasks
2. **Team Collaboration**: Extract action items with assignees from whiteboard photos
3. **Personal Productivity**: Digitize handwritten to-do lists
4. **Academic**: Convert handwritten assignment lists to digital format
5. **Business**: Process handwritten task cards from Kanban boards

## API Response Examples

### Success Response
```json
{
  "transaction_id": "uuid",
  "status": "completed",
  "processing_duration": 7.5,
  "extracted_tasks": [
    {
      "task_name": "Clean task name",
      "assignee": "Person Name",
      "due_date": "2025-12-17",
      "priority": "medium"
    }
  ]
}
```

### Error Response
```json
{
  "transaction_id": "uuid",
  "status": "failed",
  "error_message": "OCR processing failed: Invalid image format"
}
```

## Troubleshooting

### Model Not Loading
- Check GPU availability: `nvidia-smi`
- Verify model files in `weights/DotsOCR/`
- Check worker logs: `docker logs taskocr-worker`

### Slow Performance
- First request will be slow (model loading)
- Subsequent requests should be fast (~6-8s)
- Check if model is being reloaded (should only load once)

### Memory Issues
- Ensure singleton pattern is working
- Monitor VRAM: `nvidia-smi`
- Check for multiple model instances

## License

[Your License]

## Contributing

Contributions are welcome! Please read our contributing guidelines.

## Support

For issues and questions, please open a GitHub issue.
