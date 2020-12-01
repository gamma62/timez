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
#
#
# Using the REST API of https://api.sunrise-sunset.org
#

import os
import sys
import time
import re
import json
import requests


def json_load(fname):
    with open(fname, 'r') as f:
        jf = json.load(f)
        print(f"{fname} loaded")
    return jf


def json_dump(di, fname):
    with open(fname, 'w') as f:
        json.dump(di, f)
        print(f"{fname} saved")
    return


def req(D, lat, lon, forced=False):
    """ Update Sunrise-Sunset dictionary with key (lat, lon).
        The update is requested if the data is missing, outdated or forced.
    """
    baseURL = f'https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0'

    key = f'{lat};{lon}'
    timestamp = time.strftime('%Y.%m.%d %H:%M:%S', time.gmtime())

    if (key in D) and (D[key]['timestamp'] >= timestamp) and not forced:
        print(f'({lat}, {lon}) ... up-to-date')
        return False

    try:
        response = requests.get(baseURL)
        resp_json = response.json()
        assert resp_json['status'] == 'OK'
    except Exception:
        print(f'({lat}, {lon}) query failed', file=sys.stderr)
        return False

    if key not in D:
        D[key] = {}

    if 'result' in D[key] and (D[key]['result'] == resp_json['results']):
        print(f'({lat}, {lon}) ... same values, {timestamp}')
    else:
        print(f'({lat}, {lon}) ... values updated, {timestamp}')
    D[key]['result'] = resp_json['results']
    D[key]['timestamp'] = timestamp

    return True


def refresh_json(fn_json, fname=None, all_update=False, force_update=False):
    D = {}
    if fn_json and os.path.isfile(fn_json):
        D = json_load(fn_json)

    L = []
    if all_update:
        for ks in D.keys():
            L.append(tuple(ks.split(';')))
        print(f"{len(L)} keys from the dictionary")
    elif fname:
        with open(fname, 'r') as f:
            for raw in f:
                line = raw.strip()
                if len(line) == 0 or re.match(r'^[ \t]*#|[ \t]*$', line):
                    continue
                line = line.replace('"', '')
                items = re.split('\t+', line)
                lat, lon = None, None
                for item in items:
                    if re.match(r'^-?[0-9]+\.[0-9]+$', item):
                        if not lat:
                            lat = item
                        elif not lon:
                            lon = item
                    if lat and lon:
                        L.append((lat, lon))
                        break
        print(f"{len(L)} keys from {fname}")

    if len(L) == 0:
        print(f"no keys for update, nothing to do")
        return

    uc = 0
    for k in L:
        if req(D, k[0], k[1], force_update):
            uc += 1
    print(f"{uc} keys updated")

    json_dump(D, fn_json)
    return


if __name__ == '__main__':
    json_file = os.environ.get('HOME') + '/.config/TimeZ/sunrise-sunset.json'
    input_list = os.environ.get('HOME') + '/.timez'

    kwargs = {}
    i = 1
    while i < len(sys.argv):
        option = sys.argv[i]
        if option == "-h":
            print(f"""
Usage: python3 req.py [-j json_file] [-t tzlist_file] --force --all
    options:
        --all  update all keys in dict, do not read tzlist
        --force  update all keys in dict, even if timestamp up-to-date
""", file=sys.stderr)
            quit()
        elif option == "-j" and i+1 < len(sys.argv):
            i += 1
            if os.path.isfile(sys.argv[i]):
                json_file = sys.argv[i]
        elif option == "-t" and i+1 < len(sys.argv):
            i += 1
            if os.path.isfile(sys.argv[i]):
                kwargs['fname'] = sys.argv[i]
        elif option == "--all":
                kwargs['all_update'] = True
        elif option == "--force":
                kwargs['force_update'] = True
        i += 1

    refresh_json(json_file, **kwargs)

