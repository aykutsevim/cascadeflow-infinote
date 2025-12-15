# API Usage Examples

This document provides detailed examples of how to use the Task OCR Processing API.

## Table of Contents

- [Authentication](#authentication)
- [Upload Image](#upload-image)
- [Check Status](#check-status)
- [Get Job Details](#get-job-details)
- [Error Handling](#error-handling)
- [Integration Examples](#integration-examples)

## Authentication

Currently, the API does not require authentication for development. For production, you should implement authentication (JWT, API keys, etc.).

## Upload Image

### Endpoint
```
POST /api/upload/
```

### Request

**Headers:**
- `Content-Type: multipart/form-data`

**Body:**
- `image` (file): Image file of handwritten task notes

### cURL Example

```bash
curl -X POST http://localhost:8000/api/upload/ \
  -F "image=@/path/to/your/task-notes.jpg" \
  -H "Accept: application/json"
```

### Python Example

```python
import requests

url = "http://localhost:8000/api/upload/"
files = {"image": open("task-notes.jpg", "rb")}

response = requests.post(url, files=files)
data = response.json()

print(f"Transaction ID: {data['transaction_id']}")
print(f"Status: {data['status']}")
```

### JavaScript Example

```javascript
const formData = new FormData();
formData.append('image', imageFile);

fetch('http://localhost:8000/api/upload/', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => {
    console.log('Transaction ID:', data.transaction_id);
    console.log('Status:', data.status);
  })
  .catch(error => console.error('Error:', error));
```

### Response

**Success (201 Created):**
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Image uploaded successfully. Processing started."
}
```

**Error (400 Bad Request):**
```json
{
  "error": {
    "image": ["This field is required."]
  }
}
```

## Check Status

### Endpoint
```
GET /api/status/{transaction_id}/
```

### Request

**Path Parameters:**
- `transaction_id` (UUID): Transaction ID from upload response

### cURL Example

```bash
curl -X GET http://localhost:8000/api/status/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Accept: application/json"
```

### Python Example - Polling

```python
import requests
import time

transaction_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://localhost:8000/api/status/{transaction_id}/"

# Poll until completed or failed
while True:
    response = requests.get(url)
    data = response.json()

    status = data['status']
    print(f"Current status: {status}")

    if status in ['completed', 'failed']:
        break

    time.sleep(2)  # Wait 2 seconds before next poll

if status == 'completed':
    print(f"Extracted {len(data['extracted_tasks'])} tasks")
    for task in data['extracted_tasks']:
        print(f"- {task['task_name']}")
elif status == 'failed':
    print(f"Processing failed: {data['error_message']}")
```

### JavaScript Example - Polling

```javascript
async function pollJobStatus(transactionId) {
  const url = `http://localhost:8000/api/status/${transactionId}/`;

  while (true) {
    const response = await fetch(url);
    const data = await response.json();

    console.log('Current status:', data.status);

    if (data.status === 'completed') {
      console.log('Processing completed!');
      console.log('Extracted tasks:', data.extracted_tasks);
      return data;
    } else if (data.status === 'failed') {
      console.error('Processing failed:', data.error_message);
      throw new Error(data.error_message);
    }

    // Wait 2 seconds before next poll
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}

// Usage
pollJobStatus('550e8400-e29b-41d4-a716-446655440000')
  .then(result => console.log('Final result:', result))
  .catch(error => console.error('Error:', error));
```

### Response - Pending/Processing

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

### Response - Completed

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
    },
    {
      "id": 2,
      "task_name": "Update documentation",
      "description": "Update API documentation with new endpoints",
      "assignee": "Jane Smith",
      "due_date": "2024-01-22",
      "priority": "medium",
      "position_index": 1,
      "confidence_score": 0.92,
      "bbox_x": 50,
      "bbox_y": 180,
      "bbox_width": 450,
      "bbox_height": 60,
      "created_at": "2024-01-15T10:30:45Z"
    }
  ]
}
```

### Response - Failed

```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:15Z",
  "processing_duration": 15.2,
  "task_count": 0,
  "error_message": "OCR processing failed: Invalid image format"
}
```

## Get Job Details

### Endpoint
```
GET /api/jobs/{transaction_id}/
```

This endpoint always returns full job details, regardless of status.

### cURL Example

```bash
curl -X GET http://localhost:8000/api/jobs/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Accept: application/json"
```

### Response

Same format as completed status response above.

## Error Handling

### Common Error Codes

- `400 Bad Request`: Invalid input (missing image, wrong file type, file too large)
- `404 Not Found`: Transaction ID not found
- `500 Internal Server Error`: Server error during processing

### Example Error Responses

**Invalid file type:**
```json
{
  "error": {
    "image": ["Invalid file type. Allowed types: image/jpeg, image/png, image/jpg"]
  }
}
```

**File too large:**
```json
{
  "error": {
    "image": ["Image file too large. Maximum size is 10.0MB"]
  }
}
```

**Transaction not found:**
```json
{
  "detail": "Not found."
}
```

## Integration Examples

### Complete Python Client

```python
import requests
import time
from typing import Dict, Any

class TaskOCRClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')

    def upload_image(self, image_path: str) -> str:
        """Upload image and return transaction ID."""
        url = f"{self.base_url}/api/upload/"

        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(url, files=files)
            response.raise_for_status()

        data = response.json()
        return data['transaction_id']

    def get_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get job status."""
        url = f"{self.base_url}/api/status/{transaction_id}/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def wait_for_completion(self, transaction_id: str,
                           poll_interval: int = 2,
                           timeout: int = 300) -> Dict[str, Any]:
        """Wait for job to complete, polling at intervals."""
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Job did not complete within {timeout} seconds")

            data = self.get_status(transaction_id)
            status = data['status']

            if status == 'completed':
                return data
            elif status == 'failed':
                raise Exception(f"Job failed: {data.get('error_message')}")

            time.sleep(poll_interval)

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """Upload image and wait for results."""
        transaction_id = self.upload_image(image_path)
        print(f"Uploaded image. Transaction ID: {transaction_id}")

        result = self.wait_for_completion(transaction_id)
        print(f"Processing completed. Extracted {len(result['extracted_tasks'])} tasks")

        return result

# Usage
client = TaskOCRClient()
result = client.process_image('my-tasks.jpg')

for task in result['extracted_tasks']:
    print(f"Task: {task['task_name']}")
    print(f"  Assignee: {task['assignee']}")
    print(f"  Due: {task['due_date']}")
    print(f"  Priority: {task['priority']}")
    print()
```

### React/TypeScript Example

```typescript
interface Task {
  id: number;
  task_name: string;
  description: string;
  assignee: string;
  due_date: string;
  priority: string;
  confidence_score: number;
}

interface JobResult {
  transaction_id: string;
  status: string;
  extracted_tasks: Task[];
}

class TaskOCRClient {
  constructor(private baseUrl: string = 'http://localhost:8000') {}

  async uploadImage(file: File): Promise<string> {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(`${this.baseUrl}/api/upload/`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Upload failed');
    }

    const data = await response.json();
    return data.transaction_id;
  }

  async getStatus(transactionId: string): Promise<JobResult> {
    const response = await fetch(
      `${this.baseUrl}/api/status/${transactionId}/`
    );

    if (!response.ok) {
      throw new Error('Failed to get status');
    }

    return response.json();
  }

  async waitForCompletion(
    transactionId: string,
    onProgress?: (status: string) => void
  ): Promise<JobResult> {
    while (true) {
      const result = await this.getStatus(transactionId);

      if (onProgress) {
        onProgress(result.status);
      }

      if (result.status === 'completed') {
        return result;
      } else if (result.status === 'failed') {
        throw new Error('Processing failed');
      }

      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  async processImage(
    file: File,
    onProgress?: (status: string) => void
  ): Promise<Task[]> {
    const transactionId = await this.uploadImage(file);
    const result = await this.waitForCompletion(transactionId, onProgress);
    return result.extracted_tasks;
  }
}

// Usage in React component
const client = new TaskOCRClient();

async function handleImageUpload(event: React.ChangeEvent<HTMLInputElement>) {
  const file = event.target.files?.[0];
  if (!file) return;

  try {
    const tasks = await client.processImage(file, (status) => {
      console.log('Status:', status);
    });

    console.log('Extracted tasks:', tasks);
  } catch (error) {
    console.error('Error:', error);
  }
}
```

## Rate Limiting

Currently, there are no rate limits. For production, consider implementing:
- Rate limiting per IP/user
- Queue size limits
- Maximum concurrent processing jobs

## Best Practices

1. **Polling Interval**: Use 2-5 seconds between status checks
2. **Timeout**: Set a reasonable timeout (e.g., 5 minutes)
3. **Error Handling**: Always handle both network and processing errors
4. **File Validation**: Validate file type and size on client before uploading
5. **Store Transaction IDs**: Save transaction IDs for later reference

## Webhooks (Future)

For production use, consider implementing webhooks to avoid polling:

```python
# Example webhook payload (not yet implemented)
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "webhook_url": "https://your-app.com/webhook",
  "extracted_tasks": [...]
}
```
