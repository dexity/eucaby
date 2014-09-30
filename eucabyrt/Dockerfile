FROM google/nodejs

MAINTAINER Alex Dementsov <alex@eucaby.com>

RUN apt-get install -y redis-server

WORKDIR /app
ONBUILD ADD package.json /app/
ONBUILD RUN npm install
ONBUILD ADD . /app

VOLUME ["/data"]

EXPOSE 4000
EXPOSE 6379
CMD []
ENTRYPOINT ["/nodejs/bin/npm", "start"]
