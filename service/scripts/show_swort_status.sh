#! /bin/bash

ESHOST=`hostname|sed -e 's/1\./4./'`
ES="http://${ESHOST}:9200"

echo '|| Id || Status || Last Deposit Date||'
curl -s "${ES}/jper/sword_repository_status/_search?size=200" | jq '.hits.hits[]._source|.id,.status,.last_deposit_date'  | sed -e 'N;N;s/\n/ | /g' -e 's/^/| /'  -e 's/$/ |/'
