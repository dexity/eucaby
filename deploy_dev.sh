#!/usr/bin/env bash

gcloud preview app deploy app.yaml api.yaml push.yaml mail.yaml index.yaml \
    --project eucaby-dev