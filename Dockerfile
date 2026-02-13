FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    chromium \
    chromium-driver \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/chromium /usr/bin/chromium-browser

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
ENV CHROME_BIN=/usr/bin/chromium

CMD ["python", "main.py"]
