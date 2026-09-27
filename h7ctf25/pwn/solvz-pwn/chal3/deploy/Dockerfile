FROM ubuntu:24.04

RUN dpkg --add-architecture i386

RUN apt-get update && apt-get install -y \
    socat \
    uuid-runtime \
    libc6:i386 \
    libgcc-s1:i386 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ctfuser

COPY imperial_archive /home/ctfuser/
COPY entrypoint.sh /entrypoint.sh

WORKDIR /home/ctfuser

RUN chown -R ctfuser:ctfuser /home/ctfuser
RUN chmod +x /entrypoint.sh

EXPOSE 9999

ENTRYPOINT ["/entrypoint.sh"]
