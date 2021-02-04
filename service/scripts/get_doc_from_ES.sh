#! /bin/bash

ESHOST=`hostname|sed -e 's/1\./4./'`
ES="http://${ESHOST}:9200"
REPO=""
ALL=N
PROGNAME=`basename $0`
STDERR=/dev/stderr

help() {
    cat << EOT

$PROGNAME - download ElasticSearch document and prepare for update

usage: $PROGNAME [-h] -t MAPPING -i ID
 -t MAPPING    MAPPING is the "table" e.g. license, alliance, routed202101
 -n ID         document ID
 -h            this help text
EOT
}



# working on a local tunnel
if [ `hostname` == "probibw41" ]; then
    ES="http://localhost:9201"
fi

# parse arguments
while getopts "t:n:h " option; do
   case ${option} in
	t)  TYPE=$OPTARG ;;
        n)  ID=$OPTARG   ;;
        h)  help; exit 1 ;;
        *)  echo; echo "ERROR: invalid agrument or option"; help; exit 1 ;;
   esac
done 

if [ -z "$TYPE" ] || [ -z "$ID" ]; then
    help
    echo
    echo ERROR: MAPPING or ID missing
    echo
    exit 1
fi

FOUND=`curl -s "${ES}/jper/${TYPE}/${ID}" | jq .found | tr -cd 'truefalse'` 
#echo x"$FOUND"x | od -c > $STDERR 
#echo > $STDERR

if [ "$FOUND" != "true" ]; then
    echo "ERROR: document \"${ID}\" not found in mapping \"${TYPE}\"" > $STDERR
    exit 1
fi

echo "{"
echo "\"doc\": " | tr -d "\012" | sed 's/^/  /'
curl -s "${ES}/jper/${TYPE}/${ID}" | jq ._source | sed 's/^/  /'
echo "}"


