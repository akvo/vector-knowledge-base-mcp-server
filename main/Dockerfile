FROM python:3.11-slim

WORKDIR /app

# Install Postgres client (psql)
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY /entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY /test.sh /test.sh
RUN chmod +x /test.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
