FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 10001 appuser \
	&& chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

ENV GUNICORN_WORKERS=4 \
	GUNICORN_TIMEOUT=120 \
	PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 CMD curl -f http://127.0.0.1:5000/api/health || exit 1

CMD ["sh", "-c", "flask db upgrade || true; gunicorn --bind 0.0.0.0:5000 --workers ${GUNICORN_WORKERS} --timeout ${GUNICORN_TIMEOUT} --max-requests 1000 --max-requests-jitter 100 run:app"]
