#!/usr/bin/env bash

export EUCABY_BASE=$HOME/Documents/Eucaby/Data

gcloud preview app run app.yaml api.yaml \
    --datastore-path $EUCABY_BASE/Datastore/data \
    --blobstore-path $EUCABY_BASE/Blobstore
