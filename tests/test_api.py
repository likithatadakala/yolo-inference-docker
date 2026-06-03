"""
Smoke tests for YOLO inference API.

These tests verify the API works end-to-end:
- Endpoints respond with correct status codes
- Model loads successfully
- Predictions return valid JSON structure

Run locally with: pytest tests/ -v
"""
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_root_endpoint():
    """GET / returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"] == "yolov8n"
    assert data["classes"] == 80


def test_health_endpoint():
    """GET /health returns healthy (used by k8s liveness probe)."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_predict_requires_file():
    """POST /predict without a file should fail with 422 (validation error)."""
    response = client.post("/predict")
    assert response.status_code == 422


def test_predict_with_valid_image():
    """POST /predict with a real image returns detections."""
    # Use the model's own test images (always available in ultralytics package)
    import urllib.request
    url = "https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/assets/bus.jpg"
    image_bytes = urllib.request.urlopen(url).read()

    response = client.post(
        "/predict",
        files={"file": ("test.jpg", image_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "detections" in data
    assert "count" in data
    assert isinstance(data["detections"], list)
    assert data["count"] >= 1   # bus.jpg has at least one bus

    # Verify detection structure
    if data["detections"]:
        first = data["detections"][0]
        assert "class" in first
        assert "confidence" in first
        assert "bbox" in first