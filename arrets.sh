#!/bin/sh

for arret in `(for stop in stops.*.txt; do cut -d'=' -f2 < $stop | cut -d'|' -f2 | sed -e 's/ /_/g'; done;) | sort | uniq`; do
	A=$(echo $arret | sed -e 's/_/ /g');
	echo "\"$A\",";
done;
