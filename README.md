
TimeZ is a small widget to show various timezones.

Useful for people working in global groups.

See the screenshots.


Run it as easy: python timez.py

Dependencies: python, python-gtk2, python-gi, gnome-icon-theme

How does it work? Read list of cities with timezone setting and display their times in a small python-gtk widget.
The display focuses on work hours, around these the day has grey and the rest almost black background. Less then 300 lines of code.

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


About the rootes and inspiration.

I have seen some timezone clocks and tools, the closest to TimeZ is https://github.com/afcowie/slashtime which 
has an interesting interface, I got many ideas from it. Unfortunately slashtime is based on java-gnome what is not ported to FreeBSD. 
TimeZ uses python2.7 with gi.repository, some gnome dependencies like some theme icons and so. Runs on FreeBSD and on Linux.
