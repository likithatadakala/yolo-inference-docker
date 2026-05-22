# ============================================
# STAGE 1: Builder - install dependencies
# ============================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


# Install Python deps into a dedicated folder (not system-wide)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ============================================
# STAGE 2: Final - lean runtime image
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Install ONLY runtime system libraries (no compilers, no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the installed Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy the app code
COPY app.py .
COPY yolov8n.pt .

# Create a non-root user and switch to it (security best practice)
RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]