FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y gcc socat uuid-runtime && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app /app

RUN gcc -no-pie -fno-stack-protector -o overflow overflow.c

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
