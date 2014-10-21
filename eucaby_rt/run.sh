#!/usr/bin/env bash

export EUCABY_BASE=$HOME/Documents/Eucaby/Data

gcloud preview app run . \
    --datastore-path $EUCABY_BASE/Datastore/data_rt \
    --blobstore-path $EUCABY_BASE/Blobstore
