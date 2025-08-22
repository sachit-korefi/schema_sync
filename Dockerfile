# Build stage
FROM python:3.9-slim AS builder

WORKDIR /app

COPY requirements.txt .

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    # python3-dev \
    # libffi-dev \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.9-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

CMD ["sh", "-c", "df -h && uvicorn main:app --host 0.0.0.0 --port 80"]
