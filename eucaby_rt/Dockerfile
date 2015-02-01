FROM google/nodejs

MAINTAINER Alex Dementsov <alex@eucaby.com>

RUN apt-get update && apt-get install -y redis-server

WORKDIR /app
ADD package.json /app/
RUN npm install
ADD . /app

VOLUME ["/data"]

EXPOSE 4000
EXPOSE 6379
CMD ["/bin/bash", "start.sh"]

