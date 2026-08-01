FROM node:22-alpine

ENV NODE_ENV=development

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

EXPOSE 4200