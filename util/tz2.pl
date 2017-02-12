#!/usr/bin/env perl

#
# Create the tab separated list of "zone City Country lat long County"
# records with unknown coordinates will be skipped
#
# data sources:
# http://dev.maxmind.com/geoip/geoip2/geoip2-city-country-csv-databases/
#
#

use POSIX qw(strftime);

$WORLDCITIES = "../../worldcitiespop.txt";
$GEOLOCATIONS = "../../GeoLite2-City-Locations-en.csv";
$ZONEINFO = "/usr/share/zoneinfo/";

$ORIGTZ = $ENV{'TZ'};
#open(OUT, "| sort -n -r") || die;
%zoneoffsets=();
@continents = qw(Africa America Asia Atlantic Australia Europe Indian Pacific);
foreach $continent (@continents) {
	opendir(DIR, "$ZONEINFO"."$continent");
	@files = readdir(DIR);
	closedir(DIR);
	foreach $city (@files) {
		next if $city eq "." || $city eq "..";
		$zone = "$continent/$city";
		$ENV{'TZ'} = "$zone";
		#print OUT strftime ("%z", localtime()) . " $zone $city $continent\n";
		$zoneoffsets{"$zone"} = strftime ("%z", localtime());
	}
}
#close(OUT);
$ENV{'TZ'} = "$ORIGTZ";

%coord=();
$r = 0;
open(CIT, "<$WORLDCITIES") || die;
while(<CIT>) {
	next if ($r++ == 0);
	chomp();
	s/"//g;
	@arr = split(/,/);
	$ccode = $arr[0];
	$city = $arr[1];
	$lat = $arr[5];
	$long = $arr[6];
	$coord{$ccode."\t".$city} = $lat."\t".$long;
}
close(CIT);

open(OUT, "| sort -n -r") || die;
$r = 0;
open(GEO, "<$GEOLOCATIONS") || die;
while(<GEO>) {
	next if ($r++ == 0);
	chomp();
	s/"//g;
	@arr = split(/,/);
	next unless ( $arr[12] ); $zone = $arr[12];
	next unless ( $arr[10] ); $City = $arr[10];
	next unless ( $arr[4] ); $CCode = $arr[4];
	next unless ( $arr[5] ); $Country = $arr[5];
	$County = "[$arr[7]/$arr[9]]";
	$key = $CCode."\t".$City;
	$key =~ tr"A-Z"a-z";
	$offset = $zoneoffsets{$zone};
	next unless ( $offset );
	if ( $coord{$key} ) {
		($lat, $long) = split(/\t/, $coord{$key});
		print OUT "$offset\t$zone\t$City\t$Country\t$lat\t$long\t$County\n";
#	} else {
#		print OUT "$offset\t$zone\t$City\t$Country\t" . "unknown\t\t" . "$County\n";
	}
}
close(GEO);
close(OUT);
