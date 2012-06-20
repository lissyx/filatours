#!/bin/sh

for ville in `(for stop in stops.*.txt; do cut -d'=' -f2 < $stop | cut -d'|' -f3 | sed -e 's/ /_/g'; done;) | sort | uniq`; do
	V=$(echo $ville | sed -e 's/_/ /g');
	echo "\"$V\",";
done;
