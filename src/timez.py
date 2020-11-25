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
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from gi.repository.GdkPixbuf import Pixbuf

TZLIST = os.environ.get('HOME') + '/.timez'
# see /usr/share/zoneinfo or pytz.all_timezones
coretime = (9, 17)   # office core time; [from, before)
daylight = (7, 19)   # potential work hours, the rest is night

icons = {'UTC':'emblem-web',
         'home':'gtk-home'}

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
    default configuration: {TZLIST}
""", file=sys.stderr)
    quit()

def something_like_usage(reason, fn=None):
    if reason == 'enoent' or reason == 'empty':
        if reason == 'enoent':
            print(f'Configuration file [{fn}] does not exist', file=sys.stderr)
        elif reason == 'empty':
            print(f'Configuration file [{fn}] has no configuration', file=sys.stderr)
        print("""
>>> This file should contain something like this:
# lines in this file must have TAB separated fields,
# and at least 3 items: Zone City Country (optional coordinates: Lat Lon)
Pacific/Auckland	Auckland	New Zealand	-36.84	174.76
Europe/Budapest		Budapest	Hungary		47.49	19.04
America/Halifax		Halifax		Canada		44.65	-63.58
>>> Have fun!
""", file=sys.stderr)
    quit()

def get_tzlist(tzlist_file, home_zone):
    """ Parse the configuration file.
    Must be TAB separated items: zone, city, country, lat, lon
    Skip empty and comment lines. Double quotes will be removed, TABs squeezed.
    Return the configuration list and the index of first item with home_zone.
    """
    if not os.path.isfile(tzlist_file):
        something_like_usage('enoent', tzlist_file)

    tzlist = []
    utcnow = datetime.datetime.utcnow()
    home_index = -1
    with open(tzlist_file, 'r') as f:
        for raw in f:
            line = raw.strip()
            if len(line) == 0 or re.match(r'^[ \t]*#|[ \t]*$', line):
                continue
            line = line.replace('"', '')
            items = re.split('\t+', line)
            if len(items) >= 3:
                (zone, city, country) = items[:3]
            else:
                continue
            try:
                offset = base_offset(utcnow, zone)
            except pytz.UnknownTimeZoneError:
                print(f'Error: {zone} ignored', file=sys.stderr)
                continue
            tzlist.append([zone, city, country])
            if home_index == -1 and zone == home_zone:
                home_index = len(tzlist)-1

    if len(tzlist) == 0:
        something_like_usage('empty', tzlist_file)
    clen = max(14, max(( len(item[1]) for item in tzlist )))
    for item in tzlist:
        item[1] = (item[1]+" "*clen)[:clen]

    return (tzlist, home_index)

def base_offset(utcnow, zone):
    """ Calculate the actual offset in minutes from UTC.
    """
    dt = pytz.utc.localize( utcnow ).astimezone( pytz.timezone(zone) )
    return dt.utcoffset().days * 24*60 + dt.utcoffset().seconds // 60

def rel_offset(baseoff, target):
    """ Calculate the relative offset and return formatted string.
    """
    off = target - baseoff
    if off == 0:
        s = '0'
    elif off % 60 == 0:
        s = '%+d' % (off//60)
    elif off < 0:
        off = -off
        s = '-%d:%02d' % (off//60, off%60)
    else:
        s = '+%d:%02d' % (off//60, off%60)
    return s

class TimesWindow(Gtk.Window):

    def __init__(self, tzlist_file):
        Gtk.Window.__init__(self, title='TimeZ')
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        self.tzlist_file = tzlist_file
        self.tzlist = []
        self.home_index = -1
        self.local_index = 0
        self.gui = []

        # CSS for the background color changes
        screen = Gdk.Screen.get_default()
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, style_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION) 

        # office time icons
        self.utc_icon = Gtk.IconTheme.get_default().load_icon(icons['UTC'], 24, 0)
        self.home_icon = Gtk.IconTheme.get_default().load_icon(icons['home'], 24, 0)

        # common tooltip for the office grid
        tooltip = (f'office / work hours\n'
                   f'core time {coretime[0]} - {coretime[1]}\n'
                   f'day light {daylight[0]} - {daylight[1]}\n')
        self.set_tooltip_text(tooltip)

        # get configuration files
        self.tzlist, self.home_index = get_tzlist( self.tzlist_file, tzlocal.get_localzone().zone )
        self.local_index = max(0, self.home_index)

        # initialize to GUI
        # add each evbox to vbox and save evbox and its content to self.gui
        for k in range(len(self.tzlist)):
            # one evbox for each row
            evbox = Gtk.EventBox()
            evbox.set_border_width(0)
            evbox.set_size_request(-1, 10)

            # one grid in the evbox
            grid = Gtk.Grid()
            grid.set_border_width(1)

            # the office time icons
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
            grid.attach(iconview, 0, 0, 1, 2)   # grid.attach(obj, left, top, width, height)
            grid.attach(labels[0], 1, 0, 1, 1)
            grid.attach(labels[1], 2, 0, 1, 1)
            grid.attach(labels[2], 3, 0, 1, 1)
            grid.attach(labels[3], 1, 1, 1, 1)
            grid.attach(labels[4], 2, 1, 1, 1)
            grid.attach(labels[5], 3, 1, 1, 1)

            # Gtk.Window -> Gtk.Box -> [ Gtk.EventBox -> Gtk.Grid() ]
            evbox.add(grid)
            evbox.connect('button-press-event', self.on_click, k)
            evbox.connect('key-press-event', self.keyb_input, None)
            vbox.pack_start(evbox, expand=True, fill=True, padding=0)

            # save references for the updates
            self.gui.append([evbox, iconview, liststore, labels])

        self.utcnow = datetime.datetime.utcnow()
        self.redraw_gui()
        return

    def redraw_gui(self):
        """ Redraw icons, volatile labels.
        """
        # watch the base offset change (new local_index or DST jump)
        zone = self.tzlist[self.local_index][0]
        offset = base_offset( self.utcnow, zone )
        local_offset = offset

        for k in range(len(self.tzlist)):
            (zone, city, country) = self.tzlist[k][0:3]
            (evbox, iconview, liststore, labels) = self.gui[k]

            dt = pytz.utc.localize( self.utcnow ).astimezone( pytz.timezone(zone) )
            now = dt.strftime("%H:%M")

            offset = base_offset( self.utcnow, zone )
            phase = 'work' if (coretime[0] <= dt.hour < coretime[1]) else \
                    'day' if (daylight[0] <= dt.hour < daylight[1]) else \
                    'rest'

            liststore.clear()
            if zone == 'UTC':
                liststore.append([ self.utc_icon ])
            elif k == self.home_index:
                liststore.append([ self.home_icon ])
            else:
                liststore.append(row=None)

            # background color for the icons and the labels; set color with CSS
            iconview.set_name(phase)
            evbox.set_name(phase)

            # labels: foreground color, face, size with pango markup
            tupdict = hicolors[phase] if (k == self.home_index or k == self.local_index) else fgcolors[phase]
            fmt = [ '<span foreground="%s" face="%s" size="%s">' % (tup) for tup in tupdict ]
            labels[0].set_markup(fmt[0] + "%s " % city + '</span>')
            labels[1].set_markup(fmt[0] + "%-15s" % now + '</span>')
            labels[2].set_markup(fmt[0] + "%-6s" % rel_offset(local_offset, offset) + '</span>')
            labels[3].set_markup(fmt[1] + "%s " % country + '</span>')
            labels[4].set_markup(fmt[1] + dt.strftime('%a, %Y.%m.%d') + '</span>')
            labels[5].set_markup(fmt[1] + dt.tzname() + '</span>')

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
            self.redraw_gui()

    def keyb_input(self, widget, event, what):
        if event.keyval == ord('q'):
            Gtk.main_quit()

def leave(arg0, arg1):
    Gtk.main_quit()

if __name__ == '__main__':
    tzlist_file = TZLIST
    i = 1
    while i < len(sys.argv):
        option = sys.argv[i]
        if option == "-h":
            usage()
        elif os.path.isfile(option):
            tzlist_file = option
        i += 1

    window = TimesWindow(tzlist_file)
    window.connect("delete-event", leave)
    window.show_all()
    window.timerstart()
    try:
        Gtk.main()
    except KeyboardInterrupt:
        quit()

