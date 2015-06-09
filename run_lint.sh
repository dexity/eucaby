#!/usr/bin/env bash

echo 'Running pylint'
pylint eucaby_api
pylint eucaby
pylint tests


echo 'Running jshint'
jshint eucaby_mobile/www/js/*

