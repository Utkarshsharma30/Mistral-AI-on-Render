# Use official lightweight Python image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable stdout buffering
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install build dependencies for compiling llama-cpp C++ extensions if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file first for layer caching
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Environment variables default for Render
ENV PORT=8000
ENV ENGINE_MODE=proxy
ENV OLLAMA_BASE_URL=http://localhost:11434
ENV MODEL_REPO=TheBloke/Mistral-7B-Instruct-v0.2-GGUF
ENV MODEL_FILE=mistral-7b-instruct-v0.2.Q4_K_M.gguf

EXPOSE 8000

# Start command utilizing Render dynamic PORT binding
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
