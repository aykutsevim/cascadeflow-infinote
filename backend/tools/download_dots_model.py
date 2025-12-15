#!/usr/bin/env python3
"""
Download dots.ocr model weights from HuggingFace.

This script downloads the dots.ocr model and saves it locally
for use with the OCR service.
"""
import os
import sys
from pathlib import Path

def download_model():
    """Download dots.ocr model weights."""
    try:
        from transformers import AutoModelForCausalLM, AutoProcessor
    except ImportError:
        print("ERROR: transformers not installed")
        print("Install with: pip install transformers>=4.37.0")
        sys.exit(1)

    model_id = "rednote-hilab/dots.ocr"
    save_path = "./weights/DotsOCR"

    print(f"Downloading dots.ocr model: {model_id}")
    print(f"Save location: {save_path}")
    print("This will download ~7GB of data...")
    print()

    # Create directory
    os.makedirs(save_path, exist_ok=True)

    try:
        # Download model
        print("Downloading model...")
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True
        )

        # Download processor
        print("Downloading processor...")
        processor = AutoProcessor.from_pretrained(
            model_id,
            trust_remote_code=True
        )

        # Save locally
        print(f"Saving to {save_path}...")
        model.save_pretrained(save_path)
        processor.save_pretrained(save_path)

        print()
        print("✓ Model downloaded successfully!")
        print(f"✓ Saved to: {os.path.abspath(save_path)}")
        print()
        print("Next steps:")
        print("1. Set OCR_BACKEND=dots in your .env file")
        print(f"2. Set DOTS_OCR_MODEL_PATH={save_path}")
        print("3. Restart the worker service")
        print()

    except Exception as e:
        print(f"ERROR: Failed to download model: {e}")
        print()
        print("Troubleshooting:")
        print("- Check your internet connection")
        print("- Ensure you have enough disk space (~10GB)")
        print("- Try using HuggingFace CLI:")
        print(f"  huggingface-cli download {model_id} --local-dir {save_path}")
        sys.exit(1)


if __name__ == "__main__":
    download_model()
