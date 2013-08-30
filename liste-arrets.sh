#!/bin/sh

(for e in $(cat stops.*.txt | sed -e 's/ /_/g' | cut -d'|' -f2,3 | cut -d'[' -f1 | sed -e 's/_$//g');
do
	V=$(echo $e | cut -d '|' -f 2 | sed -e 's/_/ /g')
	A=$(echo $e | cut -d '|' -f 1 | sed -e 's/_/ /g')
	echo "$V - $A"
done;) | sort | uniq
