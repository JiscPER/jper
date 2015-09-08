#!/bin/bash
# create an sftp user and jail them, using username and password provided as script args
# this script also requires mkpasswd to be installed - sudo apt-get install whois will get it
# ensure this script is executable can be run as sudo without password by the software
# by doing visudo and adding this script to the commands that can be run without password, like:
# mark ALL = (root) NOPASSWD:/home/mark/jper/src/jper/service/models/createFTPuser.sh
# -------------------------------------------------------------------------
username=$1 # get from script params
egrep "^$username" /etc/passwd >/dev/null
if [ $? -eq 0 ]; then
echo "$username exists!"
exit 1
else
password=$2 # get this from script params
encryptedPassword=$(mkpasswd -m sha-512 $password)
useradd -g sftpusers -p $encryptedPassword -d /xfer -s /sbin/nologin $username
[ $? -eq 0 ] && echo "User has been added to system!" || echo "Failed to add a user!"
mkdir /home/sftpusers/$username
mkdir /home/sftpusers/$username/xfer
chown $username:sftpusers /home/sftpusers/$username/xfer
fi