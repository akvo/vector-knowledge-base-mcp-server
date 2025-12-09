FROM python:3.11-slim

WORKDIR /app

# Install Postgres client (psql)
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ./app ./app
COPY alembic.ini .
COPY migrations ./migrations

# Copy scripts
COPY entrypoint.sh /entrypoint.sh
COPY entrypoint-celery.sh /entrypoint-celery.sh

RUN chmod +x /entrypoint.sh /entrypoint-celery.sh

COPY test.sh /test.sh
RUN chmod +x /test.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
