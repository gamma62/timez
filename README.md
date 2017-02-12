
# TimeZ
is a small widget to show various timezones.

Useful for people working in global groups.

See the screenshots.


Run it as easy: python timez.py

Dependencies: python, python-gtk2, python-gi, gnome-icon-theme

How does it work? TimeZ reads list of cities with timezone setting and displays their time in a small python-gtk widget. The display focuses on work hours, around these the day has grey and the rest almost black background. Less then 300 lines of code. The location order is East to West now.


Files:

timez.py          the main python script

sample.tzlist     sample file for $HOME/.timez

start_timez.sh    sample shell script to run TimeZ in a desktop environment (FreeBSD or Linux)

timez.desktop     sample configuration to run TimeZ on mate desktop (FreeBSD)


About the rootes and inspiration.

I have seen some timezone clocks and tools, the closest to TimeZ is https://github.com/afcowie/slashtime which 
has an interesting interface, I got many ideas from it. Unfortunately slashtime is based on java-gnome what is not ported to FreeBSD. Nowadays I use python for rapid prototyping, so the langauage selection was done. TimeZ uses python2.7 with gi.repository, some gnome dependencies like some theme icons and so. TimeZ runs on FreeBSD and on Linux.

