#!/bin/bash
PATH=$PATH:/home/bluelight/local/bin
export PATH
LD_LIBRARY_PATH=/home/bluelight/local/lib
export LD_LIBRARY_PATH
set -v
python2.7 ./simple_run.py
