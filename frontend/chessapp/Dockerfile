# Step 1: Build React app
FROM node:20 AS build

WORKDIR /app

COPY package*.json ./
COPY package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Step 2: Serve with nginx
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]