FROM node:20-alpine AS base

FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

RUN npm install -g pnpm

COPY package.json pnpm-workspace.yaml ./
COPY apps/web/package.json* ./apps/web/
COPY packages/ ./packages/

RUN pnpm install

FROM base AS builder
WORKDIR /app
RUN npm install -g pnpm
COPY . .
COPY --from=deps /app /app

ENV NEXT_TELEMETRY_DISABLED 1

RUN pnpm --filter web build

FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /app /app

RUN npm install -g pnpm

USER nextjs

EXPOSE 3000

ENV PORT 3000
CMD ["pnpm", "--filter", "web", "start"]
