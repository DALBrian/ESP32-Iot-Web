FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=development \
    HOST=0.0.0.0 \
    PORT=5173

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
