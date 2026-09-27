# ===== Base image =====
FROM python:3.10-slim

# ===== system dependencies =====
RUN apt-get update && apt-get install -y --no-install-recommends \
    socat \
    uuid-runtime \
    && rm -rf /var/lib/apt/lists/*

# =====  challenge directory =====
WORKDIR /app

# =====  challenge files =====
COPY source.py /app/
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Make entrypoint executable
RUN chmod +x /docker-entrypoint.sh

# ===== Python dependencies =====
RUN pip install --no-cache-dir pycryptodome

# ===== Create unprivileged user =====
RUN useradd -m ctf
USER ctf

# ===== Expose challenge port =====
EXPOSE 10000

# ===== Run via entrypoint for dynamic flag =====
ENTRYPOINT ["/docker-entrypoint.sh"]
