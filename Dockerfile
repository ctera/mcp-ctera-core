# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy source code
COPY src/ ./src/

# Set environment variables for the application
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Expose the port that FastAPI will run on
EXPOSE 8000

# Command to run the application
CMD ["uv", "run", "uvicorn", "src.sse:app", "--host", "0.0.0.0", "--port", "8000"] 