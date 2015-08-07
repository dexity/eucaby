#!/usr/bin/env bash

# Run Eucaby API tests
nosetests -s -w tests/eucaby_api

# Run Eucaby tests
python tests/eucaby/runtests.py
