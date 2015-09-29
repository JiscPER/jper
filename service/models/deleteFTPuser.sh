#!/bin/bash
# delete an ftp user and their jail folder plus any contents
# ensure this script is executable can be run as sudo without password by the software
# by doing visudo and adding this script to the commands that can be run without password, like:
# mark ALL = (root) NOPASSWD:/home/mark/jper/src/jper/service/models/createFTPuser.sh
# -------------------------------------------------------------------------
username=$1 # get from script params
deluser $username
rm -R /home/sftpusers/$username
[ $? -eq 0 ] && echo "User has been deleted from the system!" || echo "Failed to delete a user!"
