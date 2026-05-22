# YOLO Inference Docker

[![Docker Hub](https://img.shields.io/badge/Docker_Hub-tadakalalikitha%2Fyolo--inference-blue?logo=docker)](https://hub.docker.com/r/tadakalalikitha/yolo-inference)

A containerized object detection API built with **FastAPI**, **YOLOv8n**, and **Docker**. Demonstrates production-shaped patterns for serving ML models: containerization, multi-stage builds, image size optimization, security hardening, and deterministic startup.

## Tech Stack

- **Inference:** YOLOv8n (Ultralytics) — pretrained on COCO (80 classes)
- **API:** FastAPI + Uvicorn (async, auto-generated OpenAPI docs at `/docs`)
- **Containerization:** Docker (multi-stage build, non-root user)
- **Image:** Python 3.11-slim base, ~3.2 GB final

## Quick Start

### Setup

The pretrained YOLOv8n weights aren't checked into Git (binaries don't belong in source control). Download them once before building:

​```bash
curl -L -o yolov8n.pt https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt
​```

Then continue with the build below.

```bash
# Build the image
docker build -t yolo-inference:v2 .

# Run the container
docker run -p 8000:8000 yolo-inference:v2

# Test it
curl http://localhost:8000/health
curl -X POST -F "file=@your_image.jpg" http://localhost:8000/predict
```

Or pull directly from Docker Hub:

```bash
docker pull tadakalalikitha/yolo-inference:latest
docker run -p 8000:8000 tadakalalikitha/yolo-inference:latest
```

Open `http://localhost:8000/docs` for interactive Swagger UI.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Service info, model name, class count |
| GET | `/health` | Liveness probe (for k8s, load balancers) |
| POST | `/predict` | Upload an image, get bounding boxes + classes + confidence |

Sample `/predict` response:

```json
{
  "detections": [
    {"class": "bus", "confidence": 0.87, "bbox": [22.8, 231.2, 805.0, 756.8]},
    {"class": "person", "confidence": 0.86, "bbox": [48.5, 398.5, 245.3, 902.7]}
  ],
  "count": 2
}
```

## Image Size Optimization Journey

| Version | Optimization | Image Size | Notes |
|---------|--------------|------------|-------|
| **v1** | Single-stage Dockerfile, Python 3.11-slim base | **3.23 GB** | Baseline |
| **v2** | Multi-stage build + non-root user + baked-in model weights | **3.21 GB** | Marginal size win; major security + reliability wins |
| v3 (planned) | CPU-only PyTorch via `+cpu` wheel | ~1.0 GB target | Blocked on dependency resolution; documented below |

### Why the size barely changed v1 → v2

The intuition behind multi-stage builds is to remove build-time tools (compilers, dev headers, pip cache) from the final image. **That worked, but didn't move the needle here.** The image is dominated by **PyTorch + CUDA libraries**, not build tools.

Breakdown of what's actually inside the image:

| Component | Approx. size |
|-----------|-------------|
| PyTorch (CPU + CUDA wheels) | ~2.5 GB |
| Ultralytics + OpenCV + Pillow | ~400 MB |
| Python 3.11-slim base | ~120 MB |
| YOLOv8n weights | ~6 MB |
| App code | < 1 MB |

When `pip install ultralytics` runs, it pulls PyTorch as a dependency. **By default, pip installs PyTorch's GPU wheel** (~2 GB), which bundles NVIDIA CUDA libraries. On a CPU-only deployment (or even a Mac with no NVIDIA GPU), those CUDA libraries are pure dead weight — they ship but never execute.

### The intended v3 fix (and why it's hard)

PyTorch publishes a separate **CPU-only wheel** at `https://download.pytorch.org/whl/cpu`, tagged with `+cpu` (e.g., `torch==2.8.0+cpu`). Using it shrinks the install from ~2 GB to ~200 MB.

The trick: pip's index resolution. You have to add `--extra-index-url` *in* `requirements.txt` AND pin the exact `+cpu` version, otherwise a transitive dependency (like `ultralytics`) will pull torch from PyPI and overwrite your CPU install. Version mismatches between `torch` and `torchvision` cause silent runtime failures.

Achieving v3 cleanly requires aligning specific torch/torchvision versions to what's available in PyTorch's CPU index. Documented as future work.

## Wins beyond image size

**Multi-stage build (v2):** Even though size barely changed, the build now separates dependency-install from runtime. Future optimizations (alpine base, slim torch) drop in without restructuring.

**Non-root user (v2):** Container runs as `appuser` (UID 1000), not root. If the process is ever compromised, attacker has no host privileges.

**Baked-in model weights:** Container startup is offline-capable and deterministic. The original Ultralytics pattern downloads `yolov8n.pt` from GitHub on first run, which breaks in air-gapped environments and creates a hidden runtime dependency on a third-party CDN.

**`.dockerignore`:** Excludes `.git`, `.env`, IDE configs, and Python cache from the build context — faster builds and no accidental secret leakage.

## Project Structure

```
yolo-inference-docker/
├── app.py              # FastAPI app + YOLO model loading
├── Dockerfile          # Multi-stage build (v2)
├── Dockerfile.v1       # Single-stage baseline (kept for comparison)
├── requirements.txt    # Pinned Python dependencies
├── .dockerignore       # Build context exclusions
├── yolov8n.pt          # Pretrained YOLOv8n weights (~6 MB)
└── README.md
```

## What's NOT in this repo

This is a **personal portfolio project** demonstrating Docker + ML deployment patterns on public, pretrained models. It is intentionally independent from any prior employer work. The same patterns (multi-stage builds, non-root users, baked weights, FastAPI inference endpoints) generalize to production CV pipelines I've built elsewhere.

## Future work

- Land the CPU-only PyTorch fix (target: ~1 GB image)
- Add Kubernetes manifests (Deployment, Service, HPA)
- GitHub Actions CI: build, test, push to Docker Hub on every commit
- RAG-style evals: structured test set with ground truth labels and recall@k metrics
- AWS deployment: SageMaker async endpoint or Lambda + API Gateway

## Author

Likitha Tadakala  
[LinkedIn](https://www.linkedin.com/in/tadakala-likitha/) · [GitHub](https://github.com/likithatadakala) · [Portfolio](https://likitha-tadakala.vercel.app/)
```

