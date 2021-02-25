#! /bin/bash

PROG=`basename $0`
HOST=`hostname`
ESHOST=`hostname|sed -e 's/1\./4./'`
ES="http://${ESHOST}:9200"
CURL=/bin/curl
JQ=/bin/jq
DATE=`date`

if [ "$1" == "-h" ]
then
    cat << EOT 
BACKLOG - Deepgreen Backlog 

Show number of 
 - unrouted notifications
 - documents not being processed yet by
   counting links in in /data/dg_storage/*/pending

usage: $PROG [<month> ...] [-t] [-h]
   eg. $PROG -t                  show totals only
       $PROG                     show daily numbers as well
       $PROG Sep                 show daily numbers of specific month
       $PROG Sep Oct             show daily numbers of specific months
       $PROG -h                  show help text
EOT
    exit 1
fi

# Header
cat << EOT
--------------------------
Deepreen Routing - Backlog
--------------------------

Date:  $DATE
Hosts: $HOST $ESHOST

EOT

# Notifications
echo "Total number of unrouted notifications:" | tr "\012" " " 
$CURL -s "${ES}/jper/unrouted/_count" | $JQ .count 

# Pending Documents
cd /data/dg_storage

echo "Total number of pending documents:     " | tr "\n" " "
ls -l */pending/*/*.zip 2>/dev/null | grep -c zip  2>/dev/null
has_pending_docs=$?

#if [ $? -ne 0 ]
#then
#    # No pending documents
#    exit 0  
#fi

if [ "$1"  = "-t" ]
then
    # show only totals
    exit 0
fi

# Publisher
cat << EOT

Publisher:
----------
EOT

PUBLISHERS=`ls /data/dg_publisher/`
for publisher in $PUBLISHERS
do 
    echo "$publisher:" | tr "\012" " "
    ls /data/dg_publisher/$publisher/pending/|wc -l
done

MONTHS="$*"
if [ "$1" == "" ]
then 
    MONTHS=`ls -l */pending/*/*.zip 2>/dev/null |sed 's/^.*[0-9] \([A-Z][a-z][a-z]\) [ 0-9][0-9] .*$/\1/'| sort | uniq`
fi


cat << EOT

Number of pending documents (upload date):
------------------------------------------
EOT

for all in Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec
do
    for month in $MONTHS 
    do  
        if [ $month = $all ]
        then
            for day in {1..31}
            do
                n=`ls -l */pending/*/*.zip 2>/dev/null | grep -c "${month}  *${day} "`
                if [ $? -eq 0 ]; then
                    echo "$month $day: $n"
                fi     
            done
            n=`ls -l */pending/*/*.zip 2>/dev/null | grep -c "${month} "`
            echo "$month (Sum): $n" 
            echo
        fi
    done
done

cd /home/green
cat << EOT

Number of sucessfully routed notifications:
-------------------------------------------
EOT
grep -h 'successfully routed' jperlog*  2>/dev/null |cut -c-10| sort -r | uniq -c


cat << EOT

Number of unrouted notifications:
----------------------------------
EOT
grep -h 'was not routed' jperlog*  2>/dev/null |cut -c-10| sort -r | uniq -c


