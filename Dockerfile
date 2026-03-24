FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/SEO_BOOSTER_2025 && chmod 777 /app/SEO_BOOSTER_2025

# Increase open file limits inside container
RUN echo "* soft nofile 65535" >> /etc/security/limits.conf && \
    echo "* hard nofile 2097152" >> /etc/security/limits.conf

EXPOSE 5000

# Gunicorn with safe settings for heavy proxy work
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
    "--workers", "1", \
    "--threads", "6", \
    "--timeout", "300", \
    "--max-requests", "500", \
    "--max-requests-jitter", "100", \
    "app:app"]