FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./

# Create directory for data persistence
RUN mkdir -p /app/data

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash poe-tracker && \
    chown -R poe-tracker:poe-tracker /app
USER poe-tracker

# Set default data file location
ENV DATA_FILE=/app/data/tracked_characters_data.json

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import os; exit(0 if os.path.exists('/app/poe_tracker.log') else 1)"

# Default command
CMD ["python", "main.py"]