FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

RUN npm run build -- --configuration production --output-path=/tmp/dist \
    && mkdir -p /out \
    && if [ -d /tmp/dist/browser ]; \
       then cp -r /tmp/dist/browser/. /out/; \
       else cp -r /tmp/dist/. /out/; \
       fi


FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /out/ /usr/share/nginx/html/

EXPOSE 80