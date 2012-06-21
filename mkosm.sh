#!/bin/sh


#<node id="495443062" version="2" timestamp="2011-02-14T12:11:15Z" uid="405614" user="Jean_no" changeset="7285241" lat="47.3852112" lon="0.6768484">
#<tag k="tactile_paving" v="no"/>
#<tag k="bench" v="yes"/>
#<tag k="highway" v="bus_stop"/>
#<tag k="shelter" v="yes"/>
#<tag k="name" v="Rabelais"/>
#</node>

echo '<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6">'

date=$(date +%Y-%m-%dT%H:%M:%SZ)

for line in $(grep ^Found stops_coords.txt | sed -e 's/ /_/g'); do
	# line:
	# Found_a_stop_matching_stopArea:_[StopArea|676|Voltaire|Tours|||475666,50|2267709,00|1598!0!14;1597!0!14;];_Lambert2+:_{E:475666.500000,_N:2267709.000000};_Degrees:_{E:47.397322,_N:0.689295}
	arret=$(echo $line | cut -d'|' -f3 | sed -e 's/_/ /g');
	latlon=$(echo $line | sed -e 's/.*_Degrees:_//g' -e 's/{//g' -e 's/}//g')
	lat=$(echo $latlon | cut -d',' -f1 | cut -d':' -f2 | sed -e 's/_/ /g');
	lon=$(echo $latlon | cut -d',' -f2 | cut -d':' -f2 | sed -e 's/_/ /g');
	echo "<node timestamp=\"$date\" lat=\"$lat\" lon=\"$lon\">"
	echo "	<tag k=\"highway\" v=\"bus_stop\">"
	echo "	<tag k=\"name\" v=\"$arret\">"
	echo "</node>"
done;

echo '</osm>'
