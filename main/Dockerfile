FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY /entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY /test.sh /test.sh
RUN chmod +x /test.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
