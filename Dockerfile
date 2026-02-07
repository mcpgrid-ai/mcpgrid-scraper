# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies including headless Chrome (Chromium) for SeleniumBase
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    chromium \
    chromium-driver \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/chromium /usr/bin/chromium-browser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
# Point SeleniumBase to Chromium
ENV CHROME_BIN=/usr/bin/chromium

# Run your original scraper script
CMD ["python", "main.py"]