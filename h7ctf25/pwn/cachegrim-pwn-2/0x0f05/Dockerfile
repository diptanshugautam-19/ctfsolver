FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    uuid-runtime \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir capstone prettytable

# Create challenge directory
WORKDIR /app

# Copy challenge files
COPY chal.py /app/
COPY server.py /app/
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create ctf user
RUN useradd -m ctfuser

# Expose port
EXPOSE 9999

# Run via entrypoint for dynamic flag
ENTRYPOINT ["/docker-entrypoint.sh"]
