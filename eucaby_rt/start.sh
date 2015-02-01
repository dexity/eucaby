#!/usr/bin/env bash

# Run redis
redis-server /etc/redis/redis.conf

# Run app
npm start
