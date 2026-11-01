FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
ARG API_INTERNAL_URL=http://mela-api:8000
ENV API_INTERNAL_URL=$API_INTERNAL_URL NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN addgroup -g 10001 mela && adduser -D -u 10001 -G mela mela
COPY --from=build --chown=mela:mela /app/.next/standalone ./
COPY --from=build --chown=mela:mela /app/.next/static ./.next/static
COPY --from=build --chown=mela:mela /app/public ./public
USER 10001
EXPOSE 3000
CMD ["node", "server.js"]
