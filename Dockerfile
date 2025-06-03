FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including gosu for user switching
RUN apt-get update && apt-get install -y \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./

# Create directory for data persistence
RUN mkdir -p /app/data

# Create entrypoint script for PUID/PGID support
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set default data file location
ENV DATA_FILE=/app/data/tracked_characters_data.json
ENV PUID=1000
ENV PGID=1000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import os; exit(0 if os.path.exists('/app/poe_tracker.log') else 1)"

# Use entrypoint for user creation and permission handling
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["python", "main.py"]