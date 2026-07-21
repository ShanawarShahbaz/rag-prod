FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-job-system.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-job-system.txt

# Copy application files
COPY job_application_system.py .
COPY job_scheduler.py .
COPY job_email_integration.py .
COPY cv-and-applications/ ./cv-and-applications/
COPY .env .env

# Create necessary directories
RUN mkdir -p job_application_system

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Health check endpoint (required for Cloud Run)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the scheduler
CMD ["python", "job_scheduler.py", "--mode", "schedule"]
