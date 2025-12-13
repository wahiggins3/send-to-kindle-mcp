# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY server.py ./
COPY .env.example ./

# Expose port (Cloud Run will use PORT env var)
EXPOSE 8080

# Set environment variable for production
ENV PYTHONUNBUFFERED=1

# Run the server with HTTP transport
CMD ["python", "server.py"]
