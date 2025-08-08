# build env
FROM node:21.7.1-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . ./
RUN npm run build

FROM alpine:latest
RUN mkdir -p /result_build
COPY --from=builder /app/build /result_build