#!/bin/sh

# this is for desktop environment where the window manager
# can be configured with wmctrl
# in this example: set the 'Always on top' flag

#python $HOME/lib/python2.7/timez.py &
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
