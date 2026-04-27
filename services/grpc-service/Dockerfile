FROM node:18-alpine

WORKDIR /app/services/grpc-service

COPY services/grpc-service/package*.json ./
RUN npm install --omit=dev

COPY services/grpc-service/server.js ./
COPY frontend/proto/ /app/frontend/proto/

EXPOSE 50051

CMD ["node", "server.js"]
