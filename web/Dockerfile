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

COPY web/package.json ./
COPY web/package-lock.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./next.config.ts

EXPOSE 3000

CMD ["npm", "run", "start"]
