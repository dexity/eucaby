#!/usr/bin/env bash

gcloud preview app deploy . \
    --server preview.appengine.google.com \
    --project eucaby-prd