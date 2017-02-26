#!/usr/bin/env python

# TimeZ is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# TimeZ is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for details <http://www.gnu.org/licenses/>.

import os, time, re, gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject
from gi.repository.GdkPixbuf import Pixbuf

#--- resources (adjust to your system) ---
ZONEINFO = '/usr/share/zoneinfo/'
icons = {'UTC':'emblem-web', 'home':'gtk-home'}
TZLIST = os.environ.get('HOME') + '/.timez'
workhours = (9, 18)   # "office hours"
daylight = (6, 20)   # "personal sphere", the rest is night

#--- configuration (modify with care) ---
# bg colors by phase
bgcolors = {'work': 'grey97',
            'day': 'grey75',
            'rest': 'grey42' }
# fg colors by phase: 1st and 2nd line
fgcolors = {'work': ('grey17', 'grey53'),
            'day': ('grey11', 'grey42'),
            'rest': ('grey5', 'grey23')}
# fg colors for home/local
hcolors = {'work': ('navy blue', 'medium blue'),
           'day': ('navy blue', 'medium blue'),
           'rest': ('navy blue', 'navy blue')}
# font description for the 1st and 2nd line
fface = ('monospace', 'sans')
fsize = ('medium', 'small')
#---------------------

def usage():
    print """
Usage: python timez.py [options]

Options:
  -h    show this help message and exit
  -n    do not change location order
  -r    rotate locations during the day
"""
    quit()

def something_like_usage(reason):
    if reason == 'enoent' or reason == 'empty':
        if reason == 'enoent':
            print '>>>', TZLIST, 'file does not exist'
        elif reason == 'empty':
            print '>>>', TZLIST, 'file has no zone configuration'
        print '>>> This file should contain something like this:'
        print '# lines in this file must have TAB separated fields,'
        print '# at least 3: Zone City Country'
        print '# find valid Zone names under', ZONEINFO
        print 'Pacific/Auckland	Auckland	New Zealand'
        print 'Europe/Budapest	Budapest	Hungary'
        print 'America/Halifax	Halifax	Canada'
        print '>>> Have fun!'
    quit()

def get_tzlist():
    """
    Parse the list of timezones: TAB separated items, the first 3 will be used,
    skip empty and comment lines. Return the list.
    """
    if not os.path.isfile(TZLIST):
        something_like_usage('enoent')
    tzlist = []
    citylen = 14
    with open(TZLIST, 'r') as f:
        for raw in f:
            line = raw.strip()
            if len(line) == 0 or re.match(r'^[ \t]*#', line):
                continue
            items = line.replace('"', '').split('\t')
            if len(items) < 3:
                continue
            (zone, city, country) = items[:3]
            if set_zone(zone):
                hr = time.localtime()[3]
                offset = base_offset()
                if init_reorder:
                    i = 0
                    while i < len(tzlist) and offset <= tzlist[i][-2]:
                        i = i+1
                    tzlist.insert(i, [zone, city, country, offset, hr])
                else:
                    tzlist.append([zone, city, country, offset, hr])
                if len(city) > citylen:
                    citylen = len(city)
    if len(tzlist) == 0:
        something_like_usage('empty')
    return (len(tzlist), tzlist, citylen)

def gui_rotation(tzlist, N):
    """
    Calculate the necessary row rotation based on local hours
    """
    if not loc_rotation:
        return 0
    k = 1   # skip decreasing hours
    while k < N and tzlist[k-1][-1] >= tzlist[k][-1]:
        k = k+1
    k = k%N   # and skip the rest of the day (night hours)
    while k < N and not (daylight[0] <= tzlist[k][-1] < daylight[1]):
        k = k+1
    return k%N

def set_zone(zone):
    """
    Change timezone to zone after check. Return success of setting.
    """
    if not os.path.isfile(ZONEINFO+zone):
        print 'Error:', ZONEINFO+zone, 'path not found'
        return False
    os.environ['TZ'] = zone
    time.tzset()
    return True

def base_offset():
    """
    Calculate the offset in minutes from UTC in the current timezone setting.
    """
    z = int(time.strftime('%z'), base=10)
    if z == 0:
        off = 0
    else:
        sign = z/abs(z)
        z = abs(z)
        off = sign * ((z/100)*60 + z%100)
    return off

def rel_offset(baseoff, target):
    """
    Calculate the relative offset and return formatted string.
    """
    off = target - baseoff
    if off == 0:
        s = '0'
    else:
        if off > 13*60: off = off - 24*60
        elif off < -12*60: off = off + 24*60
        if off % 60 == 0:
            s = '%+d' % (off/60)
        elif off < 0:
            off = -off
            s = '-%d:%02d' % (off/60, off%60)
        else:
            s = '+%d:%02d' % (off/60, off%60)
    return s

home_offset = base_offset()   # does not change, except with DST
class TimesWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title='TimeZ')
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        self.local_offset = home_offset
        (self.N, self.tzlist, self.citylen) = get_tzlist()
        self.timestamp = os.stat(TZLIST)[8]
        self.rotation = -1   # check once
        self.gui = []

        for i in range(self.N):
            (zone, city, country, offset, hr) = self.tzlist[i]

            evbox = Gtk.EventBox()
            evbox.set_border_width(0)
            evbox.set_size_request(-1, 10)
            grid = Gtk.Grid()
            grid.set_border_width(1)

            liststore = Gtk.ListStore(Pixbuf)
            iconview = Gtk.IconView.new()
            iconview.set_model(liststore)
            iconview.set_selection_mode(Gtk.SelectionMode.NONE)
            iconview.set_margin(0)
            iconview.set_item_padding(0)
            iconview.set_item_width(24+8)   # 8 pixels for the right side
            iconview.set_pixbuf_column(0)
            liststore.append(row=None)

            # xalign=0 is LEFT, 0.5 is CENTER, 1.0 is RIGHT
            # label.set_justify(Gtk.Justification.LEFT) is for multiline labels
            labels = [Gtk.Label(' ', xalign=0), Gtk.Label(' ', xalign=0), \
                      Gtk.Label(' ', xalign=0), Gtk.Label(' ', xalign=0), \
                      Gtk.Label(' ', xalign=0), Gtk.Label(' ', xalign=0)]

            grid.attach(iconview, 0, 0, 1, 2)
            grid.attach(labels[0], 1, 0, 1, 1)
            grid.attach(labels[1], 2, 0, 1, 1)
            grid.attach(labels[2], 3, 0, 1, 1)
            grid.attach(labels[3], 1, 1, 1, 1)
            grid.attach(labels[4], 2, 1, 1, 1)
            grid.attach(labels[5], 3, 1, 1, 1)
            evbox.add(grid)

            evbox.connect('button-press-event', self.on_click, i)
            self.gui.append([evbox, iconview, liststore, labels])

            vbox.pack_start(evbox, True, True, 0)
        #---
        self.redraw_gui()

    def refresh(self):
        sec = time.gmtime()[5]
        if sec == 0:
            self.redraw_gui()
        return True

    def redraw_gui(self):
        if loc_rotation or self.rotation == -1:
            rotation = gui_rotation(self.tzlist, self.N)
            pix_update = (self.rotation != rotation)
            self.rotation = rotation
        else:
            pix_update = False
        for i in range(self.N):
            k = (self.rotation+i) % self.N
            # the tzlist source:
            (zone, city, country, offset, hr) = self.tzlist[k]
            # the GUI target:
            (evbox, iconview, liststore, labels) = self.gui[i]

            set_zone(zone)
            hr = time.localtime()[3]
            self.tzlist[k][-1] = hr
            if workhours[0] <= hr < workhours[1]:
                phase = 'work'
            elif daylight[0] <= hr < daylight[1]:
                phase = 'day'
            else:
                phase = 'rest'

            if pix_update:
                liststore.clear()
                if zone == 'UTC':
                    liststore.append([ Gtk.IconTheme.get_default().load_icon(icons['UTC'], 24, 0) ])
                elif offset == home_offset:
                    liststore.append([ Gtk.IconTheme.get_default().load_icon(icons['home'], 24, 0) ])
                else:
                    liststore.append(row=None)

            bg = Gdk.color_parse( bgcolors[phase] )
            iconview.modify_bg(Gtk.StateType.NORMAL, bg)
            evbox.modify_bg(Gtk.StateType.NORMAL, bg)

            if offset == home_offset or offset == self.local_offset:
                fg = hcolors[phase][0], hcolors[phase][1]
            else:
                fg = fgcolors[phase][0], fgcolors[phase][1]
            fmt0 = '<span foreground="%s" face="%s" size="%s">' % (fg[0], fface[0], fsize[0])
            fmt1 = '<span foreground="%s" face="%s" size="%s">' % (fg[1], fface[1], fsize[1])
            roff = rel_offset(self.local_offset, offset)
            fmt = '%-'+str(self.citylen+1)+'s'
            labels[0].set_markup(fmt0 + fmt % city + '</span>')
            labels[1].set_markup(fmt0 + '%-15s' % time.strftime('%H:%M') + '</span>')
            labels[2].set_markup(fmt0 + '%-6s' % roff + '</span>')
            labels[3].set_markup(fmt1 + country + '</span>')
            labels[4].set_markup(fmt1 + time.strftime('%a, %Y.%m.%d') + '</span>')
            labels[5].set_markup(fmt1 + time.strftime('%Z') + '</span>')
        #---
        return

    def timerstart(self):
        # the method must return True to continue
        GObject.timeout_add(1000, self.refresh)

    def on_click(self, widget, event, gui_index):
        k = (self.rotation+gui_index) % self.N
        self.local_offset = self.tzlist[k][-2]
        self.redraw_gui()

def leave(arg0, arg1):
    Gtk.main_quit()

init_reorder = True
loc_rotation = False
if __name__ == '__main__':
    if len(os.sys.argv) > 1:
        if os.sys.argv[1] == "-n":
            init_reorder = False
        elif os.sys.argv[1] == "-r":
            loc_rotation = True
        elif os.sys.argv[1] == "-h":
            usage()
    window = TimesWindow()
    window.connect("delete-event", leave)
    window.show_all()
    window.timerstart()
    Gtk.main()
