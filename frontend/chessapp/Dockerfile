# Step 1: Build React app
FROM node:20 AS build

WORKDIR /app

COPY package*.json ./
COPY package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Step 2: Serve with Caddy
FROM caddy:alpine

COPY --from=build /app/dist /srv
COPY Caddyfile /etc/caddy/Caddyfile

EXPOSE 80