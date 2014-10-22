#!/usr/bin/env bash

export EUCABY_BASE=$HOME/Documents/Eucaby/Data

gcloud preview app run app.yaml \
    --admin-host localhost:8887 \
    --host localhost:8888 \
    --datastore-path $EUCABY_BASE/Datastore/data \
    --blobstore-path $EUCABY_BASE/Blobstore

