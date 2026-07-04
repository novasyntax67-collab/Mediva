FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/worker/requirements.txt ./apps/worker/
RUN pip install --no-cache-dir -r ./apps/worker/requirements.txt

COPY packages/backend-core/ ./packages/backend-core/
COPY apps/worker/ ./apps/worker/

WORKDIR /app/apps/worker

CMD ["celery", "-A", "celery_app.celery", "worker", "--loglevel=info"]
