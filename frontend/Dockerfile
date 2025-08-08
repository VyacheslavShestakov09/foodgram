FROM node:21.7.1-alpine
WORKDIR /app
ENV PUBLIC_URL=/
COPY package*.json ./
RUN npm install --force
COPY . ./
RUN npm run build
RUN mkdir -p /static && \
    cp -r /app/build/* /static && \
    mv /static/static/* /static/ && \
    rm -rf /static/static