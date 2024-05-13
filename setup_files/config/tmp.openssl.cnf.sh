#!/bin/bash
# Parameters
IP=$1
HOSTNAME=$2

# Create the OpenSSL configuration file with dynamic values
cat << EOF
[ req ]
default_bits       = 2048
default_md         = sha256
prompt             = no
distinguished_name = req_distinguished_name
req_extensions     = req_ext

[ req_distinguished_name ]
C  = DE
ST = Bavaria
L  = Munich
O  = BiomedLab
OU = Biomed-IoT
CN = $HOSTNAME

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1   = $HOSTNAME
IP.1    = $IP
EOF
