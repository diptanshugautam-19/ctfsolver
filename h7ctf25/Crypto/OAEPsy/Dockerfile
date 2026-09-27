FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY chall.py /app/chall.py
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

RUN pip install --no-cache-dir flask pycryptodome

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 6137

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "/app/chall.py"]
