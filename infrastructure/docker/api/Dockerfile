FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt ./apps/api/
RUN pip install --no-cache-dir -r ./apps/api/requirements.txt

COPY packages/backend-core/ ./packages/backend-core/
COPY apps/api/ ./apps/api/

WORKDIR /app/apps/api

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
