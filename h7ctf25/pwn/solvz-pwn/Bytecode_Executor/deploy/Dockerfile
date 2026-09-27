FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    socat \
    uuid-runtime \
    gcc \
    nasm \
    make \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ctfuser

WORKDIR /build

COPY *.c *.h *.asm Makefile /build/

RUN make && mv main /home/ctfuser/main

RUN rm -rf /build

COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /home/ctfuser/main && \
    chmod +x /entrypoint.sh && \
    chown -R root:root /home/ctfuser && \
    chown root:root /entrypoint.sh

WORKDIR /home/ctfuser

EXPOSE 9999

ENTRYPOINT ["/entrypoint.sh"]
