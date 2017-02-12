#!/bin/sh

python /usr/local/lib/python2.7/timez.py &
PID=$!
sleep 1

info=`wmctrl -p -l -G | awk "/$PID/ {print}"`
if [ "$info" ]
then
    wid=`echo $info | awk '{print $1}'`
    wmctrl -i -r $wid -b add,above
else
    exit 1
fi
