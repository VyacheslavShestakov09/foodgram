FROM node:21.7.1-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install --force

COPY . ./
RUN npm run build

RUN mkdir -p /static && cp -r build/* /static/

CMD ["nginx", "-g", "daemon off;"]
