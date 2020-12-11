#! /bin/bash

ESHOST=`hostname|sed -e 's/1\./4./'`
ES="http://${ESHOST}:9200"

echo '|| Id || Status || Last Deposit Date||'
curl -s "${ES}/jper/sword_repository_status/_search?size=200" | jq '.hits.hits[]._source|.id,.status,.last_deposit_date'  | sed -e 'N;N;s/\n/ | /g' -e 's/^/| /'  -e 's/$/ |/'

echo
echo '|| Id || Packaging || RepoURL ||'
curl -s 'sl64:9200/jper/account/_search?size=1000' |jq  '.hits.hits[]._source|.id,.packaging[0],.sword.collection' |  sed -e 'N;N;s/\n/ | /g' | egrep -v 'null$|""$' | sort -k3,3

