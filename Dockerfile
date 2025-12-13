# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy application code first
COPY server.py ./
COPY .env.example ./

# Install Python dependencies directly (not editable mode)
RUN pip install --no-cache-dir \
    "fastmcp>=0.2.0" \
    "ebooklib>=0.18" \
    "markdown>=3.5" \
    "python-dotenv>=1.0.0"

# Expose port (Cloud Run will use PORT env var)
EXPOSE 8080

# Set environment variable for production
ENV PYTHONUNBUFFERED=1

# Run the server with HTTP transport
CMD ["python", "server.py"]
