# KGF: Part 2 - Crown of Blood and Gold
# Hard-Tier Forensics Challenge (Challenges 9-16)

FROM node:18-alpine

WORKDIR /app

# Install system dependencies (uuidgen)
RUN apk add --no-cache util-linux

# Install dependencies directly (skip package-lock.json issues)
RUN npm install express@4.18.2 body-parser@1.20.2 --save --omit=dev

# Copy application files
COPY server.js ./
COPY public/ ./public/

# Expose port
EXPOSE 3000

# Set entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
