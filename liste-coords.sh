#!/bin/sh

(for e in $(grep "Found" stops_coords.txt | sed -e 's/ /_/g' | cut -d'|' -f3,4);
do
	V=$(echo $e | cut -d '|' -f 2 | sed -e 's/_/ /g')
	A=$(echo $e | cut -d '|' -f 1 | sed -e 's/_/ /g')
	echo "$V - $A"
done;) | sort | uniq
