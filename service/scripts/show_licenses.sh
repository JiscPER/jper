#! /bin/bash

ESHOST=`hostname|sed -e 's/1\./4./'`
ES="http://${ESHOST}:9200"
REPO=""
ALL=N
PROGNAME=`basename $0`

help() {
    cat << EOT

$PROGNAME - show licenses

usage: $PROGNAME [-a][-r REPO-ID] -h
 -e EZBID   show licensses for a repository
 -a         show all licenses

EOT
}



# working on a local tunnel
if [ `hostname` == "probibw41" ]; then
    ES="http://localhost:9201"
fi

# parse arguments
while getopts "ahe:" option; do
   case ${option} in
	e)  REPO=$OPTARG ;;
    a)  ALL=Y;;
    h)  help; exit 1 ;;
    *)  echo; echo "ERROR: invalid agrument or option"; help; exit 1 ;;
   esac
done 

if [ "$ALL" == "N" ] && [ -z "$REPO" ]; then
    help
    exit 1
fi


if [ "$ALL" == "Y" ]; then
  echo ES: $ES
  echo '| Name | Id | Type |'
  curl -s "${ES}/jper/license/_search?size=50" | jq '.hits.hits[]._source|.name,.id,.type ' | sed -e 's/^"//' -e 's/"$//' | sed -e 'N;N;s/\n/ | /g' -e 's/^/| /'  -e 's/$/ |/'

  echo
  echo '| Particpants-ID | License-Id | Identifier |'
  curl -s "$ES/jper/alliance/_search?size=50" | jq '.hits.hits[]._source|.id,.license_id,.identifier[].id' | sed -e 's/^"//' -e 's/"$//' | sed -e 'N;N;s/\n/ | /g' -e 's/^/| /'  -e 's/$/ |/'
  exit 0
fi

if [ -n "$REPO" ]; then
  echo REPO=$REPO
  echo '| License-Id | Identifier |'
  curl -s "$ES/jper/alliance/_search?size=50&q=$REPO" | jq '.hits.hits[]._source|.license_id,.identifier[].id'  | sed -e 's/^"//' -e 's/"$//' | sed -e 'N;s/\n/ | /g' -e 's/^/| /'  -e 's/$/ |/'
fi
