FROM python:3.12-slim AS base

WORKDIR /app

# System dependencies for pdfplumber
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir . \
    && pip install --no-cache-dir ".[dev]"

# Copy application code
COPY . .

# Create uploads directory for local storage
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info"]
