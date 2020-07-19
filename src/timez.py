#!/usr/bin/env python3

# TimeZ is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# TimeZ is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for details <http://www.gnu.org/licenses/>.

import os
import sys
import time
import re
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from gi.repository.GdkPixbuf import Pixbuf

#--- configuration ---
TZLIST = os.environ.get('HOME') + '/.timez'
daylight = (7, 19)   # potential work hours, the rest is night
workhours = (9, 17)   # core time [9:00 to 17:59]

#--- system resources ---
ZONEINFO_FILE = '/usr/share/zoneinfo/'
try:
    import pytz
    ZONEINFO_SET = set(pytz.all_timezones)
except:
    ZONEINFO_SET = set()
icons = {'UTC':'emblem-web', 'home':'gtk-home'}
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
#fsize = ('large', 'large')

#--- globals ------------------
initial_reorder_locations = True
rotate_locations_center_daylight = False

#---------------------

def usage():
    print("""
Usage: python3 timez.py [options]

Options:
  -h    show this help message and exit
  -n    do not change order of locations on startup
  -r    rotate locations, keep daylight in the middle
""")
    quit()

def something_like_usage(reason):
    if reason == 'enoent' or reason == 'empty':
        if reason == 'enoent':
            print('>>>', TZLIST, 'file does not exist')
        elif reason == 'empty':
            print('>>>', TZLIST, 'file has no zone configuration')
        print('>>> This file should contain something like this:')
        print('# lines in this file must have TAB separated fields,')
        print('# at least 3 fields: Zone City Country')
        print('# find valid Zone names under', ZONEINFO_FILE)
        print('Pacific/Auckland	Auckland	New Zealand')
        print('Europe/Budapest	Budapest	Hungary')
        print('America/Halifax	Halifax	Canada')
        print('>>> Have fun!')
    quit()

def get_tzlist():
    """
    Parse the list of timezones: TAB separated items, use the first three,
    skip empty and comment lines. Return the list.
    """
    if not os.path.isfile(TZLIST):
        something_like_usage('enoent')
        #--- does not return
    tzlist = []
    maxcitylen = 14
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
                offset = base_offset()
                if initial_reorder_locations:
                    i = 0
                    while i < len(tzlist) and offset <= tzlist[i][-1]:
                        i = i+1
                    tzlist.insert(i, [zone, city, country, offset])
                else:
                    tzlist.append([zone, city, country, offset])
                if len(city) > maxcitylen:
                    maxcitylen = len(city)
            else:
                print(f'Error: {zone} not found, setting ignored', file=sys.stderr)
    if len(tzlist) == 0:
        something_like_usage('empty')
        #--- does not return
    return (tzlist, maxcitylen)

def gui_rotation(hours, N):
    """
    Calculate the necessary row rotation based on hours
    """
    k = 0
    # find first night hour (maybe no one)
    for k in range(N):
        if not (daylight[0] <= hours[k][0] < daylight[1]):
            # night
            break
    first = k
    # find first hour after night (maybe no one)
    for k in range(first, N+first):
        if daylight[0] <= hours[k%N][0] < daylight[1]:
            # after night
            break
    return k%N

def set_zone(zone):
    """
    Change timezone to zone after check. Return success of setting.
    """
    if ZONEINFO_SET:
        if zone not in ZONEINFO_SET:
            return False 
    else:
        if not os.path.isfile(ZONEINFO_FILE+zone):
            # ZONEINFO_FILE+zone path not found
            return False
    os.environ['TZ'] = zone
    time.tzset()
    return True

def base_offset():
    """
    Calculate the offset in minutes from UTC in the current timezone setting, with DST.
    """ 
    # off = -time.altzone//60 if time.localtime().tm_isdst else -time.timezone//60
    # but in some rare cases this is wrong
    z = int(time.strftime('%z'), base=10)
    if z == 0:
        off = 0
    else:
        sign = -1 if z < 0 else +1
        z = abs(z)
        off = sign * ((z//100)*60 + z%100)
    return off

def rel_offset(baseoff, target):
    """
    Calculate the relative offset and return formatted string.
    """
    off = target - baseoff
    if off == 0:
        s = '0'
    else:
        if off > 13*60:
            off = off - 24*60
        elif off < -12*60:
            off = off + 24*60
        if off % 60 == 0:
            s = '%+d' % (off//60)
        elif off < 0:
            off = -off
            s = '-%d:%02d' % (off//60, off%60)
        else:
            s = '+%d:%02d' % (off//60, off%60)
    return s

class TimesWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title='TimeZ')

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        self.home_offset = base_offset()   # does not change, except with DST
        self.local_offset = self.home_offset
        (self.tzlist, self.citylen) = get_tzlist()
        self.N = len(self.tzlist)
        self.rendering = [ (0,"")+("",)*6 for i in range(self.N) ]
        self.gui = []
        self.rotation = -1   # flag for the initial (or forced) icon update

        # create the widget structure and save to self.gui
        for i in range(self.N):

            # one evbox for each clock / evbox
            evbox = Gtk.EventBox()
            evbox.set_border_width(0)
            evbox.set_size_request(-1, 10)

            # one grid in the evbox
            grid = Gtk.Grid()
            grid.set_border_width(1)

            # the icon
            liststore = Gtk.ListStore(Pixbuf)
            iconview = Gtk.IconView.new()
            iconview.set_model(liststore)
            iconview.set_selection_mode(Gtk.SelectionMode.NONE)
            iconview.set_margin(0)
            iconview.set_item_padding(0)
            iconview.set_item_width(24+8)   # 8 pixels for the right side
            iconview.set_pixbuf_column(0)
            liststore.append(row=None)

            # the labels (2 rows and 3 columns)
            # xalign=0 is LEFT, 0.5 is CENTER, 1.0 is RIGHT
            labels = [Gtk.Label(' ', xalign=0), Gtk.Label(' ', xalign=0), \
                      Gtk.Label(' ', xalign=0), Gtk.Label(' ', xalign=0), \
                      Gtk.Label(' ', xalign=0), Gtk.Label(' ', xalign=0)]

            # grid: iconview + 6 labels
            grid.attach(iconview, 0, 0, 1, 2)
            grid.attach(labels[0], 1, 0, 1, 1)
            grid.attach(labels[1], 2, 0, 1, 1)
            grid.attach(labels[2], 3, 0, 1, 1)
            grid.attach(labels[3], 1, 1, 1, 1)
            grid.attach(labels[4], 2, 1, 1, 1)
            grid.attach(labels[5], 3, 1, 1, 1)

            evbox.add(grid)
            evbox.connect('button-press-event', self.on_click, i)
            evbox.connect('key-press-event', self.keyb_input, None)

            # glue: Gtk.Window -> Gtk.Box -> [ Gtk.EventBox ... ]
            vbox.pack_start(evbox, True, True, 0)

            # save references for regular update
            self.gui.append([evbox, iconview, liststore, labels])

        self.redraw_gui()
        print(f'--- daylight [{daylight[0]}, {daylight[1]})')
        print(f'--- workhours [{workhours[0]}, {workhours[1]})')

        return

    def redraw_gui(self):
        # calculate zone dependent values into self.rendering
        for k in range(self.N):
            (zone, city, country, offset) = self.tzlist[k]
            set_zone(zone)
            hr = time.localtime()[3]

            phase = 'work' if (workhours[0] <= hr < workhours[1]) else \
                    'day' if (daylight[0] <= hr < daylight[1]) else \
                    'rest'

            # the labels
            fmt = '%-'+str(self.citylen+1)+'s'
            self.rendering[k] = (hr, phase,
                fmt % city,
                '%-15s' % time.strftime('%H:%M'),
                '%-6s' % rel_offset(self.local_offset, offset),
                country,
                time.strftime('%a, %Y.%m.%d'),
                time.strftime('%Z'),
                self.rendering[k][1])   # previous phase value

        # check if we need icon updates
        icon_update = False
        if rotate_locations_center_daylight:
            rotation = gui_rotation(self.rendering, self.N)
            icon_update = (self.rotation != rotation)
            if icon_update and self.rotation != -1:
                print(f'--- rotation: {self.rotation} -> {rotation}')
                print(f'  old: {*self.tzlist[self.rotation][:], *self.rendering[self.rotation][:2]}')
                print(f'  new: {*self.tzlist[rotation][:], *self.rendering[rotation][:2]}')
            self.rotation = rotation
        elif self.rotation == -1:
            icon_update = True
            self.rotation = 0

        for i in range(self.N):
            k = (self.rotation+i) % self.N

            (evbox, iconview, liststore, labels) = self.gui[i]
            (zone, city, country, offset) = self.tzlist[k]
            (hr, phase, s0, s1, s2, s3, s4, s5, prev_phase) = self.rendering[k]

            if prev_phase and phase != prev_phase:
                print(f'--- phase change: {prev_phase} -> {phase}')
                print(f'  {zone}, {city}, {country}, {offset}, {hr}')
                #print(f'  // [{s0}] [{s1}] [{s2}]')
                #print(f'  // [{s3}] [{s4}] [{s5}]')

            if icon_update:
                liststore.clear()
                if zone == 'UTC':
                    liststore.append([ Gtk.IconTheme.get_default().load_icon(icons['UTC'], 24, 0) ])
                elif offset == self.home_offset:
                    liststore.append([ Gtk.IconTheme.get_default().load_icon(icons['home'], 24, 0) ])
                else:
                    liststore.append(row=None)

            # background color for the icon and the labels
            bg = Gdk.color_parse( bgcolors[phase] )
            iconview.modify_bg(Gtk.StateType.NORMAL, bg)
            evbox.modify_bg(Gtk.StateType.NORMAL, bg)

            # foreground color tuple for the labels
            fg = hcolors[phase] if (offset == self.home_offset or offset == self.local_offset) else fgcolors[phase]

            # redraw the labels with markup
            fmt0 = '<span foreground="%s" face="%s" size="%s">' % (fg[0], fface[0], fsize[0])
            fmt1 = '<span foreground="%s" face="%s" size="%s">' % (fg[1], fface[1], fsize[1])
            labels[0].set_markup(fmt0 + s0 + '</span>')
            labels[1].set_markup(fmt0 + s1 + '</span>')
            labels[2].set_markup(fmt0 + s2 + '</span>')
            labels[3].set_markup(fmt1 + s3 + '</span>')
            labels[4].set_markup(fmt1 + s4 + '</span>')
            labels[5].set_markup(fmt1 + s5 + '</span>')

        return

    def refresh(self):
        sec = time.gmtime()[5]
        if sec == 0:
            self.redraw_gui()
        return True

    def timerstart(self):
        # the method must return True to continue
        GLib.timeout_add(1000, self.refresh)

    def on_click(self, widget, event, gui_index):
        button = event.get_button()[1]
        print(f'--- click button={button} ---')
        if button == 1:
            # this row shall be the start for relative offset calculations
            k = (self.rotation+gui_index) % self.N
            self.local_offset = self.tzlist[k][-1]
            self.redraw_gui()
        elif button == 3:
            # this row shall have the home icon
            k = (self.rotation+gui_index) % self.N
            self.home_offset = self.tzlist[k][-1]
            self.rotation = -1   # force icon update
            self.redraw_gui()

    def keyb_input(self, widget, event, what):
        if event.keyval == ord('q'):
            print(f'--- keyb input ---')
            Gtk.main_quit()

def leave(arg0, arg1):
    print('--- delete event ---')
    Gtk.main_quit()

if __name__ == '__main__':
    for option in os.sys.argv[1:]:
        if option == "-n":
            initial_reorder_locations = False
        elif option == "-r":
            rotate_locations_center_daylight = True
            initial_reorder_locations = True
        elif os.path.isfile(option):
            TZLIST = option
        else:
            usage()
    window = TimesWindow()
    window.connect("delete-event", leave)
    window.show_all()
    window.timerstart()
    Gtk.main()

