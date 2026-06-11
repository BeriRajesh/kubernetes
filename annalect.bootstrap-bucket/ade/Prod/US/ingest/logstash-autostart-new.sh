#!/bin/bash

# write stdout and stderr to syslog, using logger.
# taken from: http://urbanautomaton.com/blog/2014/09/09/redirecting-bash-script-output-to-syslog/
exec 1> >(logger -s -t $(basename $0)) 2>&1

# my process id (PID)
mypid=$$


# killing all logstash-autostart.sh running process, except myself
echo "Starting logstash agent with autostart in case it crashes. Killing first all running logstash and logstash-autostart processes."
for p in $(pgrep -f -l "logstash-autostart" | grep -v $$ | grep -v $mypid | grep -v "vim" | grep -v "logger" | awk '{print $1}')
do
    if ps ax | grep -v grep | grep -q $p
    then
        kill -9 $p
    fi
done
# kill all running logstash agents
pkill -f "org.logstash.Logstash"

# starting loop to self-start logstash agent if it crashes
cd /opt/logstash
until bin/logstash -f logstash-loggly.conf; do
    echo "ERROR: Logstash crashed. Exit code $? Respawning in 10 seconds."
    logname="/tmp/logstash-autostart-crash-$(date +%F-%H%M%S).log"
    echo "Generating logfile of server's status in '$logname'"

    cat > $logname <<-EOF
Date: $(date +%F-%T)

------------------------------

Created directories in last 60min:

$(find /var/lib/mesos/slaves -type d -mmin -60)

------------------------------

Free memory:

$(free)

------------------------------

Running processes sorted by memory utilization:

$(ps aux --sort -rss)

EOF
    sleep 10
    echo "Respawning Logstash after crash"
done

echo "ERROR: This line should've never been reached! It's a kind of magic!"
