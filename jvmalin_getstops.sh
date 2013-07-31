#!/bin/sh

OUT="stops_coords.jvmalin.txt"
> $OUT

for dot in ligne.graph.*.dot; do
	lineid=$(echo $dot | cut -d'.' -f3)
	for entry in $(grep "\->" $dot | sed -e 's/ /_/g' -e 's/_->_/ /g'); do
		stopname=$(echo $entry | sed -e 's/_/ /g')
		echo "[.] Treating $stopname"
		stopdone=$(grep -c "$stopname" $OUT)
		if [ "$stopdone" -eq 0 ]; then
			echo "[-] Resolving $stopname"
			result=$(python filbleu.py --get-stop-coords-jvmalin "$stopname")
			echo $result | grep -q "StopArea"
			if [ $? -eq 0 ]; then
				echo "[o] Found stopArea for $stopname, adding ..."
				echo "Trying $stopname" >> $OUT
				echo "$result" >> $OUT
			else
				echo "[!] Error for $stopname"
			fi;
		else
			echo "[|] Stop already known"
		fi;
	done;
done;
