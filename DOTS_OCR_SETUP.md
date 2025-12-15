# dots.ocr Integration Guide

This guide explains how to set up dots.ocr for advanced handwritten task recognition with GPU acceleration.

## What is dots.ocr?

dots.ocr is a powerful vision-language model that can:
- Extract text from handwritten notes
- Understand document structure and layout
- Maintain reading order
- Extract tables, formulas, and complex formatting
- Works with multiple languages

## Prerequisites

### Hardware Requirements
- **NVIDIA GPU** with CUDA support (8GB+ VRAM recommended)
- 16GB+ system RAM
- 20GB+ free disk space (for model weights)

### Software Requirements
- Docker with NVIDIA Container Toolkit
- CUDA 12.8+ drivers
- Docker Compose 2.x

## Setup Options

You have three options for OCR backends:

1. **Mock OCR** (default) - For testing without OCR
2. **EasyOCR** (CPU/GPU) - Lightweight neural OCR
3. **Tesseract** (CPU) - Traditional OCR
4. **dots.ocr** (GPU) - Advanced vision-language model

## Option 1: Install NVIDIA Container Toolkit

### For Ubuntu/Debian:

```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
    && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install NVIDIA Container Toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify installation
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
```

### For Windows with WSL2:

1. Install latest NVIDIA GPU drivers for Windows
2. Install WSL2 with Ubuntu
3. Install Docker Desktop with WSL2 backend
4. GPU passthrough is automatic with Windows 11

## Option 2: Download dots.ocr Model Weights

Create a model download script:

```bash
# Create download script
cat > backend/tools/download_dots_model.py << 'EOF'
"""Download dots.ocr model weights."""
import os
from transformers import AutoModelForCausalLM, AutoProcessor

model_id = "rednote-hilab/dots.ocr"
save_path = "./weights/DotsOCR"

print(f"Downloading dots.ocr model to {save_path}...")

# Download model
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True
)

# Download processor
processor = AutoProcessor.from_pretrained(
    model_id,
    trust_remote_code=True
)

# Save locally
os.makedirs(save_path, exist_ok=True)
model.save_pretrained(save_path)
processor.save_pretrained(save_path)

print(f"Model downloaded successfully to {save_path}")
EOF

# Run download (requires ~10GB download)
python3 backend/tools/download_dots_model.py
```

## Option 3: Configure Docker Compose for GPU

Create a GPU-enabled docker-compose override:

```yaml
# docker-compose.gpu.yml
services:
  worker:
    build:
      context: .
      dockerfile: docker/worker/Dockerfile.gpu
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - OCR_BACKEND=dots
      - DOTS_OCR_MODEL_PATH=/app/weights/DotsOCR
    volumes:
      - ./backend:/app
      - ./weights:/app/weights
```

## Option 4: Start with GPU Support

```bash
# Build GPU-enabled worker
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml build worker

# Start with GPU support
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# Verify GPU is available
docker-compose exec worker nvidia-smi
```

## Using Different OCR Backends

You can configure which OCR backend to use via environment variables:

### Use EasyOCR (lightweight, CPU/GPU):

```bash
# In .env file
OCR_BACKEND=easyocr
```

Rebuild and restart:
```bash
docker-compose up -d --build worker
```

### Use Tesseract (traditional, CPU only):

Install Tesseract in the worker container:

```bash
# Update docker/worker/Dockerfile
RUN apt-get update && apt-get install -y tesseract-ocr

# In .env file
OCR_BACKEND=tesseract
```

### Use dots.ocr (advanced, GPU required):

```bash
# In .env file
OCR_BACKEND=dots
DOTS_OCR_MODEL_PATH=/app/weights/DotsOCR
```

## Testing dots.ocr Integration

```bash
# Upload a test image
curl -X POST http://localhost:8000/api/upload/ \
  -F "image=@test_assets/tasks_photo.jpg"

# Check the logs to see which backend was used
docker-compose logs worker | grep "OCR"

# You should see: "Initialized OCR service with backend: dots"
```

## Performance Comparison

| Backend    | Speed          | Accuracy | GPU Required | Model Size |
|------------|----------------|----------|--------------|------------|
| Mock       | Instant        | N/A      | No           | 0 MB       |
| Tesseract  | ~1-2s          | Good     | No           | ~10 MB     |
| EasyOCR    | ~3-5s (CPU)    | Very Good| No*          | ~500 MB    |
| dots.ocr   | ~2-4s (GPU)    | Excellent| Yes          | ~7 GB      |

*EasyOCR can use GPU if available for better performance

## Troubleshooting

### GPU not detected:

```bash
# Check if NVIDIA runtime is available
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi

# Check Docker daemon config
cat /etc/docker/daemon.json
```

### Model download fails:

```bash
# Download manually using HuggingFace CLI
pip install huggingface-hub
huggingface-cli download rednote-hilab/dots.ocr --local-dir ./weights/DotsOCR
```

### Out of memory errors:

Reduce batch size or use a smaller model. You can also try:
```python
# In ocr_service.py, modify the model loading:
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16,  # Use FP16 instead of bfloat16
    device_map="auto",
    load_in_8bit=True,  # Enable 8-bit quantization
)
```

### Worker crashes:

Check logs:
```bash
docker-compose logs worker
```

Common issues:
- Not enough GPU memory (need 8GB+)
- CUDA version mismatch
- Model weights not downloaded

## Production Recommendations

1. **Use GPU**: dots.ocr performs best with GPU acceleration
2. **Model Caching**: Keep model weights in a persistent volume
3. **Resource Limits**: Set appropriate memory/GPU limits
4. **Monitoring**: Use Flower to monitor worker performance
5. **Scaling**: Run multiple workers if processing high volumes

## Fallback Strategy

The OCR service automatically falls back through backends:

1. Try dots.ocr (if model available and GPU present)
2. Try EasyOCR (if installed)
3. Try Tesseract (if installed)
4. Use mock data (for testing)

This ensures your application works even without GPU.

## Cost Considerations

- **dots.ocr**: Requires GPU ($0.50-1.00/hour cloud GPU)
- **EasyOCR**: Free, CPU-only is slow
- **Tesseract**: Free, traditional OCR
- **Mock**: Free, for development only

For production with high volumes, GPU-based dots.ocr provides the best accuracy/speed tradeoff.

## Next Steps

1. Test with sample handwritten notes
2. Fine-tune prompts for better extraction
3. Adjust confidence thresholds
4. Monitor accuracy and performance
5. Scale workers based on load

## Support

- dots.ocr Issues: https://github.com/rednote-hilab/dots.ocr/issues
- Project Issues: [Your issue tracker]
