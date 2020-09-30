#! /bin/bash

if [ "$1" == "" ]
then
    cat << EOT 
Deepgreen - number of document in /data/dg_storage/*/pending

usage: `basename $0` <month> [<month> ...]
   eg. `basename $0` Sep
       `basename $0` Sep Oct
EOT
    exit 1
fi


cd /data/dg_storage

for month in $* 
do
    for day in {1..31}
    do
        echo "$month $day:" | tr "\n" " "
        ls -l */pending/*/*.zip|grep "${month}  *${day} " | wc -l
    done
done
