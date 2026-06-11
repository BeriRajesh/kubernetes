#!/bin/bash

# write stdout and stderr to syslog, using logger.
# taken from: http://urbanautomaton.com/blog/2014/09/09/redirecting-bash-script-output-to-syslog/
exec 1> >(logger -s -t $(basename $0)) 2>&1

# my process id (PID)
mypid=$$
echo "my pid is $mypid"

pgrep -f -l "bamboo-autostart" | grep -v $$ | grep -v $mypid | grep -v "vim" | grep -v "logger" | awk '{print $1}'

# killing all bamboo-autostart.sh running process, except myself
echo "Starting bamboo agent with autostart in case it crashes. Killing first all running bamboo and bamboo-autostart processes."
for p in $(pgrep -f -l "bamboo-autostart" | grep -v $$ | grep -v $mypid | grep -v "vim" | grep -v "logger" | awk '{print $1}')
do
    if ps ax | grep -v grep | grep -q $p
    then
        echo $p
        kill -9 $p
    fi
done
# kill all running bamboo agents
pkill -f "org.apache.catalina.startup.Bootstrap"

# starting loop to self-start bamboo agent if it crashes
until /bamboo/atlassian-bamboo-5.14.5/bin/start-bamboo.sh -fg; do
    echo "ERROR: bamboo crashed. Exit code $? Respawning in 10 seconds."
    logname="/tmp/bamboo-autostart-crash-$(date +%F-%H%M%S).log"
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
    echo "Respawning bamboo after crash"
done

echo "ERROR: This line should've never been reached! It's a kind of magic!"
