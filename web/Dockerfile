FROM node:20-slim

WORKDIR /app

COPY web/package*.json ./
RUN npm ci

COPY web ./

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
