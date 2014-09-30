#!/usr/bin/env bash

export EUCABY_BASE=$HOME/Eucaby/Data

gcloud preview app run . \
    --datastore-path $EUCABY_BASE/Datastore/data \
    --blobstore-path $EUCABY_BASE/Blobstore
