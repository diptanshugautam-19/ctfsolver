# BackDoor Forensics Challenge
FROM python:3.11-slim

WORKDIR /app

# Copy the answer validation script and TCP server
COPY answer.py /app/
COPY server.py /app/

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Install util-linux for uuidgen
RUN apt-get update && \
    apt-get install -y uuid-runtime && \
    rm -rf /var/lib/apt/lists/*

# Expose port for TCP connections
EXPOSE 3000

ENTRYPOINT ["/docker-entrypoint.sh"]
