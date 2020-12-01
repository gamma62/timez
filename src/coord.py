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

import re

""" Coordinate Converter
Decimal Degrees (DD)			signed float
Degrees, Decimal Minutes (DDM)		(signed int, float)
Degrees, Minutes, Seconds (DMS)		(signed int, int, float)
"""

def dd(tup):
    """ Decimal Degrees (DD) from DDM or DMS
    """
    if isinstance(tup, float):
        # DD already
        return tup
    elif len(tup) == 1:
        # DD already
        return tup[0]
    elif len(tup) == 2:
        # DDM
        s, i, f = +1 if (tup[0] > 0) else -1, abs(tup[0]), float(tup[1])
        return s * (i + f / 60.0)
    elif len(tup) == 3:
        # DMS
        s, i1, i2, f = +1 if (tup[0] > 0) else -1, abs(tup[0]), tup[1], float(tup[2])
        return s * (i1 + (i2 + f / 60.0) / 60.0)
    return

def ddm(tup):
    """ Degrees, Decimal Minutes (DDM) from DD or DMS
    """
    if isinstance(tup, float):
        # DD
        tup = (tup,)
    if len(tup) == 1:
        # DD
        s, f = +1 if (tup[0] > 0) else -1, float(abs(tup[0]))
        i = int(f)
        f = (f - i) * 60.0
        return (s * i, f)
    elif len(tup) == 2:
        # DDM already
        return tup
    elif len(tup) == 3:
        # DMS
        s, i1, i2, f = +1 if (tup[0] > 0) else -1, abs(tup[0]), tup[1], float(tup[2])
        f1 = i2 + f / 60.0
        return (s * i1, f1)
    return

def dms(tup):
    """ Degrees, Minutes, Seconds (DMS) from DD or DDM
    """
    if isinstance(tup, float):
        # DD
        tup = (tup,)
    if len(tup) == 1:
        # DD
        s, f = +1 if (tup[0] > 0) else -1, float(abs(tup[0]))
        i1 = int(f)
        f1 = (f - i1) * 60.0
        i2 = int(f1)
        f2 = (f1 - i2) * 60.0
        return (s * i1, i2, f2)
    if len(tup) == 2:
        # DDM
        s, i1, f = +1 if (tup[0] > 0) else -1, abs(tup[0]), float(tup[1])
        i2 = int(f)
        f2 = (f - i2) * 60.0
        return (s * i1, i2, f2)
    elif len(tup) == 3:
        # DMS already
        return tup
    return

def unit_tests():
    f = -63.454202
    i0, f1 = -63, 27.252138
    i1, i2, f2 = -63, 27, 15.1283

    print(f'dd to dd {dd(f)}')
    print(f'dd to dd {dd((f))}')
    print(f'ddm to dd {dd((i0, f1))}')
    print(f'dms to dd {dd((i1, i2, f2))}')

    print(f'dd to ddm {ddm(f)}')
    print(f'dd to ddm {ddm((f))}')
    print(f'ddm to ddm {ddm((i0, f1))}')
    print(f'dms to ddm {ddm((i1, i2, f2))}')

    print(f'dd to dms {dms(f)}')
    print(f'dd to dms {dms((f))}')
    print(f'ddm to dms {dms((i0, f1))}')
    print(f'dms to dms {dms((i1, i2, f2))}')

def on_city(city, coords):
    [lat, lon] = re.split("[, /]+", coords)
    lat = re.split(u"[°′']", lat)
    lon = re.split(u"[°′']", lon)
    lat = dd((int(lat[0]) if lat[2]=='N' else -int(lat[0]), float(lat[1])))
    lon = dd((int(lon[0]) if lon[2]=='E' else -int(lon[0]), float(lon[1])))
    print(f'{city} {coords} -> {lat:.6f} {lon:.6f}')
    return

if __name__ == '__main__':
    on_city("Les Sables d'Olonne, France", u"46°29.81′N, 1°47.74′W")
    on_city("Manila, Philippines", u"14°35'N / 120°59'E")
    on_city("Jakarta, Indonesia", u"6°09'S / 106°49'E")

