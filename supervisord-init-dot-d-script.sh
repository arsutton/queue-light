#!/bin/bash
# chkconfig: 2345 20 80
# description: supervisord - created for bluelight

# Source function library.
. /etc/init.d/functions

start() {
    # code to start app comes here 
    # example: daemon program_name &
    sudo -u bluelight bash -c "/home/bluelight/cclight/run_supervisord.sh &"
}

stop() {
    # code to stop app comes here 
    # example: killproc program_name
    /home/bluelight/cclight/run_supervisord_ctl_stop.sh
}

case "$1" in 
    start)
       start
       ;;
    stop)
       stop
       ;;
    restart)
       stop
       start
       ;;
    status)
       # code to check status of app comes here 
       # example: status program_name
       /home/bluelight/cclight/run_supervisord_ctl_status.sh
       ;;
    *)
       echo "Usage: $0 {start|stop|status|restart}"
esac
