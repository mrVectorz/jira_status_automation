# Containerfile for JIRA Status Automation
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
COPY requirements-web.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-web.txt

# Copy application files
COPY *.py .
COPY *.sh .

# Create necessary directories
RUN mkdir -p /app/reports /app/config

# Create non-root user for security
RUN groupadd -r jira-automation && useradd -r -g jira-automation jira-automation

# Copy actual config file if it exists, otherwise use example
COPY config.json* /app/config/
RUN if [ ! -f /app/config/config.json ]; then \
    cp /app/config/config.example.json /app/config/config.json; \
    fi

# Set ownership after copying everything
RUN chown -R jira-automation:jira-automation /app
USER jira-automation

# Set default web port
ENV WEB_PORT=8080

# Default command - run web server with correct config path
CMD ["sh", "-c", "python3 web_server.py --config /app/config/config.json --reports-dir /app/reports --host 0.0.0.0 --port ${WEB_PORT}"]

# Expose web port (using environment variable)
EXPOSE ${WEB_PORT}
