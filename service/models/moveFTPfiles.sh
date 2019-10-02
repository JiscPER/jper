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
targetdir=$3
uniqueid=$4
uniquedir=$5
thefile="$6"
# 2019-07-17 TD : new param for directory indicating pending items (e.g. by symbolic links)
pendingdir=$7
egrep "^$username" /etc/passwd >/dev/null
# only do if the username exists (just to check)
if [ $? -eq 0 ]; then

# TODO: could add a check for the username to see if matching user is logged in, by calling the w command
# in which case do nothing on this iteration because the user is probably in the process of sending files

# 2016-11-03 TD : disabled this safety step for now!
# # for time being copy everything to an ftp archive for this user first
# # so there is an original copy of everything received before processing by the system
# #mkdir -p /home/mark/tmparchive/$username/$uniqueid
# #cp -R $thefile /home/mark/tmparchive/$username/$uniqueid
# mkdir -p /home/green/thearchive/$username/$uniqueid
# cp -R $thefile /home/green/thearchive/$username/$uniqueid

# check that the tmp processing dir for this user and for this unique move process exists
mkdir -p $uniquedir
# 2019-07-19 TD : check that the pending directory exists
mkdir -p $pendingdir
# move the specified file in the jail to the temp processing directory
mv "$thefile" $uniquedir
# 2019-07-19 TD : create/overwrite symbolic link indicating the item as pending
ln -sf $uniquedir $pendingdir/.
# set ownership from the user targetdir down
chown -R $newowner:$newowner $targetdir
fi
