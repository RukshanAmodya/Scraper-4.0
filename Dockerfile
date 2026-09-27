FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY faymas_scraper.py .

# Mountable volume for data persistence
VOLUME ["/app/scraped_data"]

# Default check interval in seconds (60s)
ENV CHECK_INTERVAL=60

# Run in 24/7 daemon mode
CMD ["sh", "-c", "python faymas_scraper.py --daemon --interval ${CHECK_INTERVAL}"]
