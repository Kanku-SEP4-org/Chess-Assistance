FROM node:18-alpine

WORKDIR /app/api-gateway

COPY api-gateway/package*.json ./
RUN npm install --omit=dev

COPY api-gateway/server.js ./
COPY frontend/proto/ /app/frontend/proto/

EXPOSE 3001

CMD ["node", "server.js"]
