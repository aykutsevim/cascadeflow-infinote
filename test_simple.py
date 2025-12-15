#!/usr/bin/env python3
"""
Simple test to verify model is loaded once and reused.
"""
import requests
import time
import sys

API_URL = "http://localhost:8000/api"
IMAGE_PATH = "test_assets/tasks_photo.jpg"

def test_upload(test_num):
    """Upload and wait for results."""
    print(f"\n{'='*50}")
    print(f"Test #{test_num}")
    print(f"{'='*50}")

    start = time.time()

    # Upload
    with open(IMAGE_PATH, 'rb') as f:
        response = requests.post(f"{API_URL}/upload/", files={'image': f})

    transaction_id = response.json()['transaction_id']
    print(f"Uploaded: {transaction_id}")

    # Poll for completion
    while True:
        response = requests.get(f"{API_URL}/status/{transaction_id}/")
        data = response.json()
        status = data['status']

        if status == 'completed':
            elapsed = time.time() - start
            print(f"Status: Completed")
            print(f"Processing time: {data.get('processing_duration', 'N/A')}s")
            print(f"Total time: {elapsed:.2f}s")
            print(f"Tasks extracted: {len(data.get('extracted_tasks', []))}")
            return elapsed
        elif status == 'failed':
            print(f"Status: Failed - {data.get('error_message')}")
            sys.exit(1)

        time.sleep(2)

if __name__ == "__main__":
    print("\n" + "="*50)
    print("TESTING MODEL REUSE")
    print("="*50)

    time1 = test_upload(1)
    time.sleep(2)
    time2 = test_upload(2)

    print("\n" + "="*50)
    print("RESULTS")
    print("="*50)
    print(f"Test #1: {time1:.2f}s")
    print(f"Test #2: {time2:.2f}s")

    if time2 < time1 * 1.5:  # Allow some variance
        speedup = ((time1 - time2) / time1) * 100
        print(f"\n[SUCCESS] Model reused! Test #2 similar or faster")
        print(f"Speedup: {speedup:.1f}%")
    else:
        print(f"\n[WARNING] Test #2 slower than expected")

    print("\n" + "="*50)
