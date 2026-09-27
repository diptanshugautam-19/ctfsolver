FROM --platform=amd64 ubuntu:20.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libseccomp-dev \
    socat \
    uuid-runtime \
    && rm -rf /var/lib/apt/lists/*

# Create challenge directory
WORKDIR /app

# Copy source and compile
COPY test.c /app/chal.c
RUN gcc -o /app/chal /app/chal.c -no-pie -fno-stack-protector -lseccomp -O0 -w

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create ctf user
RUN useradd -m ctfuser

# Expose port
EXPOSE 1337

# Run via entrypoint for dynamic flag
ENTRYPOINT ["/docker-entrypoint.sh"]