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

#--- resources ---
ZONEINFO = '/usr/share/zoneinfo/'
TZLIST = os.environ.get('HOME') + '/.tzlist'
icons = {'UTC':'emblem-web', 'home':'gtk-home'}

#--- configuration ---
workhours = (9, 18)
daylight = (6, 20)   # rest is night
daystart = 2         # after midnight
# bg colors by phase
bgcolors = {'work':'grey97', \
            'day':'grey75', \
            'rest':'grey42' }
# fg colors by phase: 1st and 2nd line
fgcolors = {'work':('grey17', 'grey53'), \
            'day':('grey11', 'grey42'), \
            'rest':('grey5', 'grey23')}
# fg colors for home/local
hcolors = {'work':('navy blue', 'medium blue'), \
           'day':('navy blue', 'medium blue'), \
           'rest':('navy blue', 'navy blue')}
# font description for the 1st and 2nd line
fface = ('monospace', 'sans')
fsize = ('medium', 'small')
#---------------------

def get_tzlist():
    """
    Parse the list of timezones: TAB separated items, the first 3 will be used,
    skip empty and comment lines. Return the list.
    Maybe, the last item could be the optional icon name?
    """
    if not os.path.isfile(TZLIST):
        print '>>>', TZLIST, 'file does not exist'
        print '>>> This file should contain something like this:'
        print '# lines in this file must have 3 TAB separated fields:'
        print '# "Zone" "City" "Country"'
        print '# find valid zone names in', ZONEINFO
        print '"Europe/Budapest"	"Budapest"	"Hungary"'
        print '"Pacific/Auckland"	"Auckland"	"New Zealand"'
        print '>>> Have fun!'
        quit()
    #---
    tzlist = []
    if set_zone('UTC'):
        hr = int(time.strftime('%H'))
        offset = base_offset()
        tzlist.append(['UTC', 'UTC', 'Universal Time', offset, hr])
    with open(TZLIST, 'r') as f:
        for raw in f:
            line = raw.strip()
            if len(line) == 0 or re.match(r'^[ \t]*#', line):
                continue
            items = line.replace('"', '').split('\t')
            # other fields are discarded now, maybe later... the Gtk icon name?
            (zone, city, country) = items[:3]
            if zone != 'UTC' and set_zone(zone):
                hr = int(time.strftime('%H'))
                offset = base_offset()
                # decreasing order by offset (minutes)
                i = 0
                while i < len(tzlist) and (offset+1440)%1440 >= (tzlist[i][3]+1440)%1440:
                    i = i+1
                tzlist.insert(i, [zone, city, country, offset, hr])
    return tzlist

def tzlist_rotation(tzlist):
    N = len(tzlist)
    k = 1
    while k < N and tzlist[k-1][-1] <= tzlist[k][-1]:
        k = k+1
    while k < N and tzlist[k][-1] < daystart:
        k = k+1
    return k

def set_zone(zone):
    """
    Change timezone to zone after check. Return success of setting.
    """
    if not os.path.isfile(ZONEINFO+zone):
        print 'Error:', ZONEINFO+zone, 'path not found, entry ignored'
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

class TimesWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title='TimeZ')
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        self.local_offset = base_offset()
        self.home_offset = self.local_offset
        self.tzlist = get_tzlist()
        self.rotation = 0
        self.gui = []

        N = len(self.tzlist)
        for i in range(N):
            (zone, city, country, offset, hr) = self.tzlist[i]
            #print '>>> "{}"\t"{}"\t"{}"'.format(zone, city, country, offset)

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

    def redraw_gui(self):
        N = len(self.tzlist)
        rotation = tzlist_rotation(self.tzlist)
        pix_update = (self.rotation != rotation)
        self.rotation = rotation
        for i in range(N):
            k = (self.rotation+i) % N
            # the tzlist source:
            (zone, city, country, offset, hr) = self.tzlist[k]

            set_zone(zone)
            hr = int(time.strftime('%H'))
            self.tzlist[k][-1] = hr
            if workhours[0] <= hr < workhours[1]:
                phase = 'work'
            elif daylight[0] <= hr < daylight[1]:
                phase = 'day'
            else:
                phase = 'rest'

            # the GUI target:
            (evbox, iconview, liststore, labels) = self.gui[i]
            if pix_update:
                liststore.clear()
                if zone == 'UTC':
                    liststore.append([ Gtk.IconTheme.get_default().load_icon(icons['UTC'], 24, 0) ])
                elif offset == self.home_offset:
                    liststore.append([ Gtk.IconTheme.get_default().load_icon(icons['home'], 24, 0) ])
                else:
                    liststore.append(row=None)

            bg = Gdk.color_parse( bgcolors[phase] )
            iconview.modify_bg(Gtk.StateType.NORMAL, bg)
            evbox.modify_bg(Gtk.StateType.NORMAL, bg)

            if offset == self.home_offset or offset == self.local_offset:
                fg = hcolors[phase][0], hcolors[phase][1]
            else:
                fg = fgcolors[phase][0], fgcolors[phase][1]
            fmt0 = '<span foreground="%s" face="%s" size="%s">' % (fg[0], fface[0], fsize[0])
            fmt1 = '<span foreground="%s" face="%s" size="%s">' % (fg[1], fface[1], fsize[1])

            # column width set by upper fields, monospace font char count: 17, 13, 6
            roff = rel_offset(self.local_offset, offset)
            labels[0].set_markup(fmt0 + '%-17s' % city + '</span>')
            labels[1].set_markup(fmt0 + '%-13s' % time.strftime('%H:%M') + '</span>')
            labels[2].set_markup(fmt0 + '%-6s' % roff + '</span>')
            labels[3].set_markup(fmt1 + country + '</span>')
            labels[4].set_markup(fmt1 + time.strftime('%a, %Y.%m.%d') + '</span>')
            labels[5].set_markup(fmt1 + time.strftime('%Z') + '</span>')
        #---
        return True

    def timerstart(self):
        # the method must return True to continue
        GObject.timeout_add(60000, self.redraw_gui)

    def on_click(self, widget, event, gui_index):
        N = len(self.tzlist)
        k = (self.rotation+gui_index) % N
        offset = self.tzlist[k][3]
        zone = self.tzlist[k][0]
        #print '>>> click: (i:{} k:{} {}) offset {} -> {}'.format(gui_index, k, zone, self.local_offset, offset)
        self.local_offset = offset
        self.redraw_gui()

def leave(arg0, arg1):
    Gtk.main_quit()

if __name__ == '__main__':
    window = TimesWindow()
    window.connect("delete-event", leave)
    window.show_all()
    window.timerstart()
    Gtk.main()

