#!/usr/bin/env bash

#
# Create list of zones sorted by offset based on files in zoneinfo tree
#
#

# get the main list (offset, zone, city, continent) and sort by offset
# separate fields with TAB and offset groups by newline
base_zone_list()
{
	TZDIR=/usr/share/zoneinfo
	for continent in Africa America Asia Atlantic Australia Europe Indian Pacific ; do
		cd $TZDIR/$continent
		for city in * ; do
			offset=$(TZ="$continent/$city" date +"%z")
			echo "$offset $continent/$city $city $continent"
		done
	done | sort -n -r |\
	awk 'BEGIN{OFS="\t"}
	{	if (NR>1 && $1!=grp)
			{print ""}
		grp=$1;
		split($3, arr, "/");
		gsub("_"," ",arr[2]);
		print $1, "\""$3"\"", "\""arr[2]"\"", "\""arr[1]"\"";
	}'
}

base_zone_list
