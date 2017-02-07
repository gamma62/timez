#!/usr/bin/env bash

#
# Create list of zones sorted by offset; get longest City names
#

offset()
{
	zone=$1
	TZ="$zone" date +"%z %Z $zone"
}

TZDIR=/usr/share/zoneinfo
for cont in Africa America Asia Atlantic Australia Europe Indian Pacific ; do
	cd $TZDIR/$cont
	for city in * ; do
		offset "$cont/$city"
	done
done | sort -n > zones.tmp

# max length of City name
awk '{split($3, a, "/"); if (length(a[2]) >= len) {len = length(a[2]); print len, a[2], $3}}' zones.tmp

# group zones
awk '{if (NR>1 && $1!=grp) {print ""} grp=$1; print}' zones.tmp > list_of_zones

rm zones.tmp
