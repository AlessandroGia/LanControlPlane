FROM node:22-alpine AS deps

WORKDIR /app

COPY web/package.json ./
COPY web/package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY web/package.json ./
COPY web/package-lock.json ./
COPY web/tsconfig.json ./
COPY web/next.config.ts ./
COPY web/app ./app
COPY web/components ./components
COPY web/lib ./lib
COPY web/public ./public

RUN npm run build

FROM node:22-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
