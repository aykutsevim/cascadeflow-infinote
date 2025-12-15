#!/usr/bin/env python3
"""
Test script to upload image TWICE and verify model is loaded only once.
The second call should be faster and use the same memory.
"""
import requests
import time
import sys
import json
from pathlib import Path

API_URL = "http://localhost:8000/api"
IMAGE_PATH = "test_assets/tasks_photo.jpg"
MAX_ATTEMPTS = 60  # Increased for first call with model loading
POLL_INTERVAL = 2


def upload_image(image_path, test_number):
    """Upload image to the API."""
    print(f"\n{'='*60}")
    print(f"TEST #{test_number}: Uploading image...")
    print(f"{'='*60}\n")

    # Check if file exists
    path = Path(image_path)
    if not path.exists():
        print(f"[ERROR] Image file not found at {image_path}")
        sys.exit(1)

    file_size = path.stat().st_size / 1024  # KB
    print(f"[OK] Found image: {image_path} ({file_size:.2f} KB)")

    # Upload
    upload_start = time.time()
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(f"{API_URL}/upload/", files=files)
            response.raise_for_status()

        data = response.json()
        transaction_id = data['transaction_id']
        status = data['status']
        upload_end = time.time()

        print(f"[OK] Upload successful! (took {upload_end - upload_start:.2f}s)")
        print(f"  Transaction ID: {transaction_id}")
        print(f"  Status: {status}\n")

        return transaction_id, upload_start

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Upload failed!")
        print(f"  Error: {e}")
        sys.exit(1)


def poll_for_results(transaction_id, upload_start_time, test_number):
    """Poll the API for processing results."""
    print(f"Polling for results (Test #{test_number})...")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(f"{API_URL}/status/{transaction_id}/")
            response.raise_for_status()
            data = response.json()

            current_status = data['status']
            print(f"  Attempt {attempt}/{MAX_ATTEMPTS} - Status: {current_status}")

            if current_status == 'completed':
                end_time = time.time()
                total_time = end_time - upload_start_time

                print(f"\n[OK] Processing completed!")
                print(f"  Total processing time: {total_time:.2f} seconds")

                display_results(data)
                return True, total_time

            elif current_status == 'failed':
                print("\n[ERROR] Processing failed!")
                print(f"  Error: {data.get('error_message', 'Unknown error')}")
                return False, None

            elif current_status in ['pending', 'processing']:
                time.sleep(POLL_INTERVAL)

            else:
                print(f"  Unknown status: {current_status}")
                time.sleep(POLL_INTERVAL)

        except requests.exceptions.RequestException as e:
            print(f"  Error checking status: {e}")
            time.sleep(POLL_INTERVAL)

    print(f"\n[ERROR] Timeout waiting for results after {MAX_ATTEMPTS * POLL_INTERVAL} seconds")
    return False, None


def display_results(data):
    """Display the OCR processing results."""
    print("\n--- Results Summary ---")
    print(f"Processing Duration: {data.get('processing_duration', 'N/A')} seconds")
    print(f"OCR Confidence: {data.get('ocr_confidence', 'N/A')}")

    tasks = data.get('extracted_tasks', [])
    print(f"Tasks Extracted: {len(tasks)}")

    if tasks:
        print("\nExtracted Tasks:")
        for i, task in enumerate(tasks, 1):
            print(f"  {i}. {task.get('task_name', 'N/A')} (Priority: {task.get('priority', 'N/A')})")


def main():
    """Main function - runs two tests back-to-back."""
    print("\n" + "="*60)
    print("DOUBLE TEST: Verifying model is loaded only once")
    print("="*60)
    print("\nExpected behavior:")
    print("  - Test #1: Model loads (slower)")
    print("  - Test #2: Model reused (faster, same memory)")
    print()

    try:
        # Test #1
        transaction_id_1, start_time_1 = upload_image(IMAGE_PATH, 1)
        success_1, time_1 = poll_for_results(transaction_id_1, start_time_1, 1)

        if not success_1:
            print("\n[ERROR] Test #1 failed. Aborting.")
            sys.exit(1)

        # Wait a moment before second test
        print("\n" + "-"*60)
        print("Waiting 3 seconds before Test #2...")
        print("-"*60)
        time.sleep(3)

        # Test #2
        transaction_id_2, start_time_2 = upload_image(IMAGE_PATH, 2)
        success_2, time_2 = poll_for_results(transaction_id_2, start_time_2, 2)

        if not success_2:
            print("\n[ERROR] Test #2 failed.")
            sys.exit(1)

        # Compare results
        print("\n" + "="*60)
        print("COMPARISON RESULTS")
        print("="*60)
        print(f"\nTest #1 (First call):  {time_1:.2f} seconds")
        print(f"Test #2 (Second call): {time_2:.2f} seconds")

        if time_2 < time_1:
            speedup = ((time_1 - time_2) / time_1) * 100
            print(f"\n[SUCCESS] Test #2 was {speedup:.1f}% faster")
            print("  This confirms the model is being reused correctly.")
        else:
            print(f"\n[WARNING] Test #2 was not faster ({time_2:.2f}s vs {time_1:.2f}s)")
            print("  The model might still be loading on each call.")

        print("\n" + "="*60)
        print("MEMORY CHECK")
        print("="*60)
        print("Check your system monitor/GPU monitor:")
        print("  - VRAM should remain stable (not increase)")
        print("  - RAM should remain stable (not increase)")
        print("  - Both tests should use approximately the same memory")

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
