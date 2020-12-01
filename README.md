
# TimeZ
is a small widget to show various timezones.

Useful for people working in global groups.

See the screenshots.



Run it as easy: python timez.py

Dependencies: python, python-gtk3, python-gi, gnome-icon-theme

How does it work? TimeZ reads list of cities with timezone setting and displays their time in a pyGtk widget.

The recommended top-down location order is East to West.

Options: 
  [-n] timez configuration

Original TimeZ was less then 300 lines of code.



Files:

timez.py          the main python script

sample.tzlist     sample file for $HOME/.timez

timez             sample shell script to run TimeZ in a desktop environment (FreeBSD or Linux)

timez.desktop     sample configuration to run TimeZ on mate desktop (FreeBSD)


About the rootes and inspiration.

I have seen some timezone clocks and tools, the closest to TimeZ is https://github.com/afcowie/slashtime which 
has an interesting interface, I got many ideas from it. Unfortunately slashtime is based on java-gnome what is not ported to FreeBSD. Nowadays I use python for rapid prototyping, so the language selection was done.
TimeZ uses python3 with gi.repository, some gnome dependencies like some theme icons. TimeZ runs on FreeBSD and on Linux.

