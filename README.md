
TimeZ is a small widget to show various timezones.
Useful for people working in global groups.

See the screenshots.

Run it as easy: python timez.py

Dependencies: python, python-gtk2, python-gi, gnome-icon-theme

Install as a package:

cp timez.py   /usr/local/lib/python2.7/timez.py
cp start_timez.sh   /usr/local/bin/start_timez.sh
chmod 755   /usr/local/bin/start_timez.sh
cp timez.desktop   /usr/local/share/applications/timez.desktop

Copy sample.tzlist to $HOME/.tzlist and edit it. Add remove lines.

Files:

timez.py          the main python script
start_timez.sh    shell script to run TimeZ in desktop environment
timez.desktop     the configuration to run TimeZ in desktop environment
sample.tzlist     sample file for $HOME/.tzlist

