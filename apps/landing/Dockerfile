FROM oven/bun:1.3.8 AS bun

FROM node:24-bookworm-slim AS build
WORKDIR /app
COPY --from=bun /usr/local/bin/bun /usr/local/bin/bun

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

ARG PUBLIC_SITE_URL=https://heftra.com
ARG PUBLIC_APP_URL=https://app.heftra.com
ARG PUBLIC_API_URL=https://api.heftra.com
ENV PUBLIC_SITE_URL=$PUBLIC_SITE_URL \
    PUBLIC_APP_URL=$PUBLIC_APP_URL \
    PUBLIC_API_URL=$PUBLIC_API_URL \
    ASTRO_TELEMETRY_DISABLED=1

COPY . .
RUN ./node_modules/.bin/astro build

FROM nginxinc/nginx-unprivileged:1.31.6-alpine AS serve
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q --spider http://127.0.0.1:8080/healthz || exit 1
