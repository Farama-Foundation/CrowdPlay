FROM node:16.8.0 as build

WORKDIR /usr/src/crowdplay

COPY . .

RUN npm install
RUN npm run build

FROM nginx:1.19.6

COPY --from=build /usr/src/crowdplay/dist /usr/share/nginx/html
COPY nginx/proxy_params /etc/nginx/proxy_params

# The image will run /docker-entrypoint.d/20-envsubst-on-templates.sh
# which runs envsubst on /etc/nginx/templates/nginx.conf.template to 
# /etc/nginx/conf.d/nginx.conf
COPY nginx/nginx.conf.template /etc/nginx/templates/nginx.conf.template
