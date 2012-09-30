#!/bin/sh

for arret in `(for stop in stops.*.txt; do cut -d'=' -f2 < $stop | cut -d'|' -f2,3 | sed -e 's/ /_/g' -e 's/_\[.*\]//g'; done;) | sort | uniq`; do
	V=$(echo $arret | cut -d'|' -f2 | sed -e 's/_/ /g');
	A=$(echo $arret | cut -d'|' -f1 | sed -e 's/_/ /g');
	echo "Trying \"$V - $A\""
	python ../filbleu.py --get-stop-coords "$V - $A"
done;
