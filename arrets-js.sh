#!/bin/sh

for line in $(grep ^Found stops_coords.txt | sed -e 's/ /_/g'); do
	ville=$(echo $line | cut -d'|' -f4 | sed -e 's/_/ /g');
	arret=$(echo $line | cut -d'|' -f3 | sed -e 's/_/ /g');
	latlon=$(echo $line | sed -e 's/.*_Degrees:_//g' -e 's/{//g' -e 's/}//g')
	lat=$(echo $latlon | cut -d',' -f1 | cut -d':' -f2 | sed -e 's/_/ /g');
	lon=$(echo $latlon | cut -d',' -f2 | cut -d':' -f2 | sed -e 's/_/ /g');
	echo "    _stops.push(new BusStop(\"$arret\", \"$ville\", $lat, $lon))";
done;
