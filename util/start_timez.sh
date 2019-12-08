#!/bin/sh

python2.7 ~/.local/lib/python2.7/timez.py &
PID=$!
sleep 1

if [ -e /proc/$PID ]; then
	info=`wmctrl -p -l -G | awk "/$PID/ {print}"`
	if [ "$info" ]; then
		wid=`echo $info | awk '{print $1}'`
		wmctrl -i -r $wid -b add,above
		wmctrl -i -r $wid -b add,skip_taskbar
		wmctrl -i -r $wid -b add,skip_pager
		exit 0
	fi
fi
exit 1
