#!/bin/bash
PATH=$PATH:/home/bluelight/local/bin
export PATH
LD_LIBRARY_PATH=/home/bluelight/local/lib
export LD_LIBRARY_PATH
set -v
/home/bluelight/local/bin/supervisorctl -c /home/bluelight/etc/supervisord.conf
