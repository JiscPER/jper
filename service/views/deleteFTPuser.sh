#!/bin/bash
# delete an ftp user. Does not delete their folder though. It should be emtpied by other processes anyway
# because all the users could do is sftp files for upload
# this script also requires mkpasswd to be installed - sudo apt-get install whois will get it
# ensure this script can be run as sudo without password by the software
# sudo chown root.cloo createFTPuser.sh
# sudo chmod 4775 createFTPuser.sh
# -------------------------------------------------------------------------
username=$1 # get from script params
deluser $username
[ $? -eq 0 ] && echo "User has been deleted from the system!" || echo "Failed to delete a user!"
