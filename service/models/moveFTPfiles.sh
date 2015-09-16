#!/bin/bash
# move all files of an ftp user from their jail to tmp, where they will be processed
# set the owner and permissions to something that the scheduler will be allowed to move 
# e.g. same owner as the one that is going to be running the script would be good
# ensure this script is executable can be run as sudo without password by the software
# by doing visudo and adding this script to the commands that can be run without password, like:
# mark ALL = (root) NOPASSWD:/home/mark/jper/src/jper/service/models/moveFTPfiles.sh
# -------------------------------------------------------------------------
username=$1 # get from script params
newowner=$2
sftpdir=$3
tmpdir=$4
uniquedir=$5
egrep "^$username" /etc/passwd >/dev/null
# only do if the username exists (just to check)
if [ $? -eq 0 ]; then

# TODO: could add a check for the username to see if matching user is logged in, by calling the w command
# in which case do nothing on this iteration because the user is probably in the process of sending files

# for time being copy everything to an ftp archive for this user first
# so there is an original copy of everything received before processing by the system
mkdir -p /home/mark/tmparchive/$username
cp $sftpdir/$username/xfer/* /home/mark/tmparchive/$username

# check that the tmp processing dir for this user and for this unique move process exists
mkdir -p $uniquedir
# move everything in the jail to the temp processing directory
mv $sftpdir/$username/xfer/* $uniquedir
# set ownership from the user tmpdir down
chown -R $newowner:$newowner $tmpdir
fi