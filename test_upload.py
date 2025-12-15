#!/usr/bin/env python3
"""
Test script to upload image and check OCR processing results.
"""
import requests
import time
import sys
import json
from pathlib import Path

API_URL = "http://localhost:8000/api"
IMAGE_PATH = "test_assets/tasks_photo.jpg"
MAX_ATTEMPTS = 30
POLL_INTERVAL = 2


def upload_image(image_path):
    """Upload image to the API."""
    print("=== Testing Task OCR API ===\n")

    # Check if file exists
    path = Path(image_path)
    if not path.exists():
        print(f"❌ Error: Image file not found at {image_path}")
        sys.exit(1)

    file_size = path.stat().st_size / 1024  # KB
    print(f"✓ Found image: {image_path} ({file_size:.2f} KB)\n")

    # Upload
    print("Step 1: Uploading image...")
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(f"{API_URL}/upload/", files=files)
            response.raise_for_status()

        data = response.json()
        transaction_id = data['transaction_id']
        status = data['status']

        print(f"✓ Upload successful!")
        print(f"  Transaction ID: {transaction_id}")
        print(f"  Status: {status}\n")

        return transaction_id

    except requests.exceptions.RequestException as e:
        print(f"❌ Upload failed!")
        print(f"  Error: {e}")
        sys.exit(1)


def poll_for_results(transaction_id):
    """Poll the API for processing results."""
    print("Step 2: Polling for results...")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(f"{API_URL}/status/{transaction_id}/")
            response.raise_for_status()
            data = response.json()

            current_status = data['status']
            print(f"  Attempt {attempt}/{MAX_ATTEMPTS} - Status: {current_status}")

            if current_status == 'completed':
                print("\n✓ Processing completed!\n")
                display_results(data)
                return True

            elif current_status == 'failed':
                print("\n❌ Processing failed!")
                print(f"  Error: {data.get('error_message', 'Unknown error')}")
                return False

            elif current_status in ['pending', 'processing']:
                time.sleep(POLL_INTERVAL)

            else:
                print(f"  Unknown status: {current_status}")
                time.sleep(POLL_INTERVAL)

        except requests.exceptions.RequestException as e:
            print(f"  Error checking status: {e}")
            time.sleep(POLL_INTERVAL)

    print(f"\n❌ Timeout waiting for results after {MAX_ATTEMPTS * POLL_INTERVAL} seconds")
    return False


def display_results(data):
    """Display the OCR processing results."""
    print("=== Results ===")
    print(f"Processing Duration: {data.get('processing_duration', 'N/A')} seconds")
    print(f"OCR Confidence: {data.get('ocr_confidence', 'N/A')}")

    tasks = data.get('extracted_tasks', [])
    print(f"Tasks Extracted: {len(tasks)}\n")

    if tasks:
        print("=== Extracted Tasks ===")
        for i, task in enumerate(tasks, 1):
            print(f"\nTask #{i}")
            print(f"  Name: {task.get('task_name', 'N/A')}")

            if task.get('description'):
                print(f"  Description: {task['description']}")

            if task.get('assignee'):
                print(f"  Assignee: {task['assignee']}")

            if task.get('due_date'):
                print(f"  Due Date: {task['due_date']}")

            print(f"  Priority: {task.get('priority', 'N/A')}")
            print(f"  Confidence: {task.get('confidence_score', 'N/A')}")

    print("\n=== Full JSON Response ===")
    print(json.dumps(data, indent=2))


def main():
    """Main function."""
    try:
        transaction_id = upload_image(IMAGE_PATH)
        success = poll_for_results(transaction_id)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
