#! /bin/bash

ESHOST=`hostname|sed -e 's/1\./4./'`
ES="http://${ESHOST}:9200"
LIMIT=1000
FULL=0
PROGNAME=`basename $0`

help() {
    cat << EOT

$PROGNAME - show failed notifications

usage: $PROGNAME [-i LIMIT] [-f] [-u] -q <query>
 -u          show notification and URL only (default)
 -f          show full notifications
 -l LIMIT    limit results to LIMIT (default $LIMIT)
 -q <query>  query string <query> may be a DOI, ISSN, 
             TIMESTAMP and must not contain white space

EOT
}



# working on a local tunnel
if [ `hostname` == "probibw41" ]; then
    ES="http://localhost:9201"
fi

# parse arguments
while getopts "hl:fq:" option; do
    case ${option} in
	f)  FULL=1  ;;
	l)  LIMIT=$OPTARG  ;;
        q)  QUERY="$OPTARG"  ;;
        h)  help; exit 1 ;;
        *)  echo; echo "ERROR: invalid agrument or option"; help; exit 1 ;;
    esac
done

#cat <<EOT
#ES:  $ES
#q:   $QUERY
#l:   $LIMIT
#f:   $FULL
#ARGS: $*
#EOT



if [ -z "$QUERY" ]; then
    echo
    echo "ERROR: query string <query> for searching failed notifications is missing"
    help
    exit 1
fi

# print number of hits
echo "Hits:"| tr '\012' ' '
curl -s "${ES}/jper/failed/_search?size=$LIMIT&q=\"$QUERY\"" |jq '.hits|.total'

echo
if [ $FULL == 1 ]; then
    # print full notification
    curl -s "${ES}/jper/failed/_search?size=$LIMIT&q=\"$QUERY\"" |jq '.hits.hits[]._source'
else
    # print notification id an package URL only
    curl -s "${ES}/jper/failed/_search?size=$LIMIT&q=\"$QUERY\"" |jq '.hits.hits[]|._id,._source.links[].url'
fi
