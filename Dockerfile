# Production Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase and models
COPY backend/ ./backend/
COPY models/ ./models/

# Expose port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/app/models/base/Qwen2.5-3B
ENV ADAPTER_PATH=/app/models/adapters/telecom-ticket-triage

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
