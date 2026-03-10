FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    wget \
    gnupg \
    ca-certificates \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get install -y chromium chromium-driver --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Wrap the real Chromium binary to always include container-required flags
RUN printf '#!/bin/bash\nexec /usr/bin/chromium --no-sandbox --disable-dev-shm-usage --disable-gpu "$@"\n' > /usr/bin/google-chrome \
    && chmod +x /usr/bin/google-chrome

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Create venv in /app (writable after chown)
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu"

CMD ["python", "main.py"]
