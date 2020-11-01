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
import tzlocal
import datetime
import pytz
import re
import requests
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from gi.repository.GdkPixbuf import Pixbuf

TZLIST = os.environ.get('HOME') + '/.timez'
# see /usr/share/zoneinfo or pytz.all_timezones
daylight = (7, 19)   # potential work hours, the rest is night
workhours = (9, 17)   # core time [9:00 to 17:59]
icons = {'UTC':'emblem-web', 'home':'gtk-home'}

# bg colors by phase -- use CSS
css = b'''
    #work { background: grey97; }
    #day { background: grey75; }
    #rest { background: grey42; }
'''

# (foreground, face, size) font attributes for the 1st and 2nd line, normal labels
fgcolors = {'work': (('grey17', 'monospace', 'medium'), ('grey53', 'sans', 'small')),
            'day':  (('grey11', 'monospace', 'medium'), ('grey42', 'sans', 'small')),
            'rest': (('grey5', 'monospace', 'medium'),  ('grey23', 'sans', 'small'))}
hicolors = {'work': (('navy blue', 'monospace', 'medium'), ('medium blue', 'sans', 'small')),
            'day':  (('navy blue', 'monospace', 'medium'), ('medium blue', 'sans', 'small')),
            'rest': (('navy blue', 'monospace', 'medium'), ('navy blue',   'sans', 'small'))}

def usage():
    print(f"""
Usage: python3 timez.py [configuration_file]
    Default configuration file: {TZLIST}
""", file=sys.stderr)
    quit()

def something_like_usage(reason):
    if reason == 'enoent' or reason == 'empty':
        if reason == 'enoent':
            print(f'Configuration file [{TZLIST}] does not exist', file=sys.stderr)
        elif reason == 'empty':
            print(f'Configuration file [{TZLIST}] has no configuration', file=sys.stderr)
        print("""
>>> This file should contain something like this:
# lines in this file must have TAB separated fields,
# and at least 3 items: Zone City Country
Pacific/Auckland	Auckland	New Zealand
Europe/Budapest		Budapest	Hungary
America/Halifax		Halifax		Canada
>>> Have fun!
""", file=sys.stderr)
    quit()

def get_tzlist(home_zone):
    """
    Parse the configuration file: TAB separated items, zone, city, country, lat, lon
    skip empty and comment lines. Double quotes will be removed, TABs squeezed.
    Return the configuration list and the index of first item with home_zone.
    """
    if not os.path.isfile(TZLIST):
        something_like_usage('enoent')

    tzlist = []
    utcnow = datetime.datetime.utcnow()
    home_index = -1
    with open(TZLIST, 'r') as f:
        for raw in f:
            line = raw.strip()
            if len(line) == 0 or re.match(r'^[ \t]*#|[ \t]*$', line):
                continue
            line = line.replace('"', '')
            items = re.split('\t+', line)
            if len(items) >= 5:
                (zone, city, country, lat, lon) = items[:5]
            else:
                (zone, city, country, lat, lon) = items[:3] + ['0.0', '0.0']
            try:
                offset = base_offset(utcnow, zone)
            except pytz.UnknownTimeZoneError:
                print(f'Error: {zone} ignored', file=sys.stderr)
                continue
            tzlist.append([zone, city, country, lat, lon, offset, ''])
            if home_index == -1 and zone == home_zone:
                home_index = len(tzlist)-1

    if len(tzlist) == 0:
        something_like_usage('empty')

    clen = max((len(item[1]) for item in tzlist))
    clen = max(14, clen)
    for item in tzlist:
        item[1] = (item[1]+" "*clen)[:clen]

    return (tzlist, home_index)

def base_offset(utcnow, zone):
    """
    Calculate the actual offset in minutes from UTC of given zone.
    """
    dt = pytz.utc.localize( utcnow ).astimezone( pytz.timezone(zone) )
    return dt.utcoffset().days * 24*60 + dt.utcoffset().seconds // 60

def rel_offset(baseoff, target):
    """
    Calculate the relative offset and return formatted string.
    """
    off = target - baseoff
    if off == 0:
        s = '0'
    else:
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

        self.tzlist, self.home_index = get_tzlist( tzlocal.get_localzone().zone )
        self.N = len(self.tzlist)
        self.local_index = max(0, self.home_index)
        self.local_offset = self.tzlist[self.local_index][5]
        self.gui = []

        # CSS for the background color changes
        screen = Gdk.Screen.get_default()
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, style_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION) 

        self.utc_icon = Gtk.IconTheme.get_default().load_icon(icons['UTC'], 24, 0)
        self.home_icon = Gtk.IconTheme.get_default().load_icon(icons['home'], 24, 0)

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
            iconview = Gtk.IconView()
            iconview.set_model(liststore)
            iconview.set_selection_mode(Gtk.SelectionMode.NONE)
            iconview.set_margin(0)
            iconview.set_item_padding(0)
            iconview.set_item_width(24+8)   # 8 pixels for the right side
            iconview.set_pixbuf_column(0)
            liststore.append(row=None)

            # the labels (2 rows and 3 columns)
            labels = [Gtk.Label(label=' ', xalign=0), \
                      Gtk.Label(label=' ', xalign=0), \
                      Gtk.Label(label=' ', xalign=0), \
                      Gtk.Label(label=' ', xalign=0), \
                      Gtk.Label(label=' ', xalign=0), \
                      Gtk.Label(label=' ', xalign=0)]

            # grid: iconview + 6 labels
            grid.attach(iconview, 0, 0, 1, 2)
            grid.attach(labels[0], 1, 0, 1, 1)
            grid.attach(labels[1], 2, 0, 1, 1)
            grid.attach(labels[2], 3, 0, 1, 1)
            grid.attach(labels[3], 1, 1, 1, 1)
            grid.attach(labels[4], 2, 1, 1, 1)
            grid.attach(labels[5], 3, 1, 1, 1)

            # Gtk.Window -> Gtk.Box -> [ Gtk.EventBox -> Gtk.Grid() ]
            evbox.add(grid)
            evbox.connect('button-press-event', self.on_click, i)
            evbox.connect('key-press-event', self.keyb_input, None)
            vbox.pack_start(evbox, True, True, 0)

            # save references for updates
            self.gui.append([evbox, iconview, liststore, labels])

        self.utcnow = datetime.datetime.utcnow()
        self.print_base_configuration()
        self.redraw_gui(icon_update=True)
        return

    def print_base_configuration(self):
        print(f'--- daylight [{daylight[0]}, {daylight[1]})')
        print(f'--- workhours [{workhours[0]}, {workhours[1]})')
        return

    def redraw_gui(self, icon_update=False):

        # notify about the base offset change (after selecting new row or DST jump of that row)
        zone = self.tzlist[self.local_index][0]
        offset = base_offset( self.utcnow, zone )
        if offset != self.local_offset:
            dt = pytz.utc.localize( self.utcnow ).astimezone( pytz.timezone(zone) )
            print(f'  local offset change: ({zone}) {self.local_offset} -> {offset} ({dt.tzname()})')
            self.local_offset = offset

        for k in range(self.N):
            (zone, city, country) = self.tzlist[k][0:3]
            offset = base_offset( self.utcnow, zone )
            dt = pytz.utc.localize( self.utcnow ).astimezone( pytz.timezone(zone) )
            hr = dt.hour
            phase = 'work' if (workhours[0] <= hr < workhours[1]) else \
                    'day' if (daylight[0] <= hr < daylight[1]) else \
                    'rest'

            # show offset value change (DST, any row)
            prev_offset = self.tzlist[k][5]
            if offset != prev_offset:
                print(f'  offset change: {city} {prev_offset} -> {offset} ({dt.tzname()})')
            self.tzlist[k][5] = offset

            # show phase value change (regular, any row)
            prev_phase = self.tzlist[k][6]
            if prev_phase and phase != prev_phase:
                comment = 'time-slip' if self.utcnow.second else f'hour={hr}'
                print(f'  phase change: {city} {prev_phase} -> {phase} ({comment})')
            self.tzlist[k][6] = phase

            (evbox, iconview, liststore, labels) = self.gui[k]
            if icon_update:
                liststore.clear()
                if zone == 'UTC':
                    liststore.append([ self.utc_icon ])
                elif k == self.home_index:
                    liststore.append([ self.home_icon ])
                else:
                    liststore.append(row=None)

            # background color for the icon and the labels, set color with CSS
            iconview.set_name(phase)
            evbox.set_name(phase)

            # labels: foreground color, face, size with pango markup
            highlight = (k == self.home_index or k == self.local_index)
            fmt0 = '<span foreground="%s" face="%s" size="%s">' % (hicolors[phase][0] if highlight else fgcolors[phase][0])
            fmt1 = '<span foreground="%s" face="%s" size="%s">' % (hicolors[phase][1] if highlight else fgcolors[phase][1])
            labels[0].set_markup(fmt0 + "%s " % city + '</span>')
            labels[1].set_markup(fmt0 + '%-15s' % dt.strftime('%H:%M') + '</span>')
            labels[2].set_markup(fmt0 + '%-6s' % rel_offset(self.local_offset, offset) + '</span>')
            labels[3].set_markup(fmt1 + "%s " % country + '</span>')
            labels[4].set_markup(fmt1 + dt.strftime('%a, %Y.%m.%d') + '</span>')
            labels[5].set_markup(fmt1 + dt.tzname() + '</span>')
        return

    def refresh(self):
        # refresh in every minute, and also on every hour:minute jump, like resume
        utcnow = datetime.datetime.utcnow()
        if utcnow.second == 0 or (self.utcnow.hour != utcnow.hour or self.utcnow.minute != utcnow.minute):
            self.utcnow = utcnow
            self.redraw_gui()
        return True

    def timerstart(self):
        # interval in miliseconds, the function must return True to continue
        GLib.timeout_add(interval=1000, function=self.refresh)

    def on_click(self, widget, event, gui_index):
        button = event.get_button()[1]
        if button == 1:
            # this row shall be the base for relative offset calculation
            self.local_index = gui_index
            print(f'--- set local base: {self.tzlist[gui_index][1]}')
            self.redraw_gui()
        elif button == 2:
            self.print_base_configuration()
        elif button == 3:
            pass

    def keyb_input(self, widget, event, what):
        if event.keyval == ord('q'):
            print(f'--- keyb input ---')
            Gtk.main_quit()

def leave(arg0, arg1):
    print('--- delete event ---')
    Gtk.main_quit()

if __name__ == '__main__':
    for option in os.sys.argv[1:]:
        if option == "-h" or option == "--help":
            usage()
        else:
            TZLIST = option
    window = TimesWindow()
    window.connect("delete-event", leave)
    window.show_all()
    window.timerstart()
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print('--- keyb interrupt ---')
        quit()

