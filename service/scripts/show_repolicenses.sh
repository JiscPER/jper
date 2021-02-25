#! /bin/bash

ESHOST=`hostname|sed -e 's/1\./4./'`
ES="http://${ESHOST}:9200"
echo ES: $ES
echo '| Name | Id | Type |'
curl -s "${ES}/jper/license/_search?size=50" | jq '.hits.hits[]._source|.name,.id,.type ' | sed -e 's/^"//' -e 's/"$//' | sed -e 'N;N;s/\n/ | /g' -e 's/^/| /'  -e 's/$/ |/'

echo
echo '| Particpants-ID | License-Id | Identifier |'
curl -s 'sl64.kobv.de:9200/jper/alliance/_search?size=20' | jq '.hits.hits[]._source|.id,.license_id,.identifier[].id' | sed -e 's/^"//' -e 's/"$//' | sed -e 'N;N;s/\n/ | /g' -e 's/^/| /'  -e 's/$/ |/'
