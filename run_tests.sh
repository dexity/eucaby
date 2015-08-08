#!/usr/bin/env bash

echo 'Running Eucaby API tests'
nosetests -s -w tests/eucaby_api

echo 'Running Eucaby tests'
python tests/eucaby/runtests.py
