#! /bin/bash

ES="http://sl64.kobv.de:9200"

echo '| Name | Id | Type |'
curl -s "${ES}/jper/license/_search?size=50" | jq '.hits.hits[]._source|.name,.id,.type ' | sed -e 's/^"//' -e 's/"$//' | sed -e 'N;N;s/\n/ | /g' -e 's/^/| /'  -e 's/$/ |/'

