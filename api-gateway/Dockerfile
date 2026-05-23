FROM node:18-alpine
WORKDIR /app/api-gateway

COPY api-gateway/package*.json ./
RUN npm ci --omit=dev

COPY api-gateway/server.js ./
COPY api-gateway/services/ ./services/
COPY shared/ /app/shared/

EXPOSE 3001
CMD ["node", "server.js"]
