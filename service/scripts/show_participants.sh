#! /bin/bash

ESHOST=`hostname|sed -e 's/1\./4./'` 
ES="http://${ESHOST}:9200"
echo $ES

if [ -z "$1" ]
then
    cat <<EOT
Deepgreen - show participants to a specific license

usage: `basename $0` LicenseID
  e.g. `basename $0` a83cfa70d9b4400a9966505565ec4ada
EOT
    exit 1
fi

id=$1
echo
echo LicenseID $id
echo
echo '| EZB-Id | ISIL | Name |'
curl -s "${ES}/jper/alliance/_search?q=${id}"| jq '.hits.hits[]._source.participant[] | .identifier[].id,.name' | sed -e 's/^"//' -e 's/"$//' | sed -e 'N;N;s/\n/ | /g' -e 's/^/| /'  -e 's/$/ |/'
echo
