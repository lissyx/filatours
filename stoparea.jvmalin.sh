#!/bin/sh

for arret in $(for gpx in filbleu_route.TTRNav*.gpx; do xmllint --format $gpx | grep name | cut -d'>' -f2 | cut -d'<' -f1 | sed -e 's/ /_/g'; done | sort | uniq); do
	K=$(echo $arret | sed -e 's/_/ /g');
	echo "Trying \"$K\""
	python ../filbleu.py --get-stop-coords-jvmalin "$K"
done;
