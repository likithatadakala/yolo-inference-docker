from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import io

# Create the FastAPI app instance
app = FastAPI(title="YOLO Inference API", version="1.0")

# Load model ONCE at startup, not per request
model = YOLO("yolov8n.pt")


@app.get("/")
def root():
    return {
        "status": "ok",
        "model": "yolov8n",
        "classes": len(model.names)
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # Read the uploaded image bytes
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))

    # Run YOLO inference
    results = model(image)

    # Format results into clean JSON
    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "class": model.names[int(box.cls[0])],
                "confidence": float(box.conf[0]),
                "bbox": box.xyxy[0].tolist()
            })

    return JSONResponse({
        "detections": detections,
        "count": len(detections)
    })