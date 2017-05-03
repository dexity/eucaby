#!/usr/bin/env bash

gcloud preview app deploy \
    app.yaml api.yaml push.yaml mail.yaml \
    index.yaml dispatch.yaml queue.yaml cron.yaml \
    --project eucaby-prd --version=1
