#!/usr/bin/env bash

USAGE="Usage: $0 [dev|prd] <ip_address>"

if [ $# -ne 2 ]; then
    echo $USAGE
fi

if [[ $1 -ne 'dev' ]] || [[ $1 -ne 'prd' ]]; then
    echo $USAGE
fi

SSL_CA="~/.ssh/eucaby-$1-server-ca.pem"
SSL_CERT="~/.ssh/eucaby-$1-client-cert.pem"
SSL_KEY="~/.ssh/eucaby-$1-client-key.pem"

mysql -u root -p -h $2
# Enable ssl options when Cloud SQL enable SSL certificates
# --ssl-ca=$SSL_CA --ssl-cert=$SSL_CERT --ssl-key=$SSL_KEY
