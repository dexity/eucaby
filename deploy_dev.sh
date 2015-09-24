#!/usr/bin/env bash

gcloud preview app deploy \
    app.yaml api.yaml push.yaml mail.yaml \
    index.yaml dispatch.yaml queue.yaml cron.yaml \
    --project eucaby-dev --version=1 --set-default