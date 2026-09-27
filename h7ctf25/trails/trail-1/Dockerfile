FROM python:3.10-slim

WORKDIR /app

COPY app/ /app/

RUN apt-get update && \
    apt-get install -y netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 1337

CMD ["python3", "server.py"]
