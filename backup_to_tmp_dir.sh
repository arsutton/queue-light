#!/bin/bash
#
# modified 09/14/2015
#
set -v
cd ~/Documents
TODAY=$(date +"%Y-%m-%d")
BACKUP_DIR=/tmp/bluelight/$TODAY
echo $BACKUP_DIR
mkdir -p $BACKUP_DIR
cd /home/bluelight/
tar cvfz $BACKUP_DIR/0-bluelight-home-dir-backup-$TODAY.tgz ./* >$BACKUP_DIR/0-backup-bluelight-$TODAY.out.txt 2>&1
tail $BACKUP_DIR/0-backup-bluelight-$TODAY.out.txt
