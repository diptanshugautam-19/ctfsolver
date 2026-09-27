# Multi-stage build for optimized standalone deployment
FROM node:18-alpine AS deps
WORKDIR /app
RUN npm install -g pnpm
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install

FROM node:18-alpine AS builder
WORKDIR /app
RUN npm install -g pnpm
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Build with standalone output
RUN pnpm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV production

# Install only runtime dependencies
RUN apk add --no-cache util-linux && \
    addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER nextjs

EXPOSE 8080
ENV PORT 8080

ENTRYPOINT ["/docker-entrypoint.sh"]