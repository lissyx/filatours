#!/bin/sh

# LINES=$(cat lines.txt | sed -e 's/ /_/g' | cut -d')' -f1 | cut -d'(' -f2 | grep ^id= | cut -d'=' -f2 | sort -n)
LINES=1

#for LINE in $LINES; do
#	name=$(grep "(id=$LINE)" lines.txt | sed -e "s/Line(id=$LINE): //g" -e 's/name={.*} //g' -e 's/name={.*}$//g' -e "s/name='.*'//g" -e 's/number=//g' -e 's/;//g' -e 's/ | / /g' -e 's/ $//g')
#	for subline in $name; do 
#		for stop in $(cat stops.$LINE.txt | sed -e 's/ /_/g' | cut -d'=' -f2 | sed -e 's/^>_//g'); do
#			# line:
#			# Found_a_stop_matching_stopArea:_[StopArea|676|Voltaire|Tours|||475666,50|2267709,00|1598!0!14;1597!0!14;];_Lambert2+:_{E:475666.500000,_N:2267709.000000};_Degrees:_{E:47.397322,_N:0.689295}
#			line=$(grep "$(echo $stop | sed -e 's/_/ /g')" stops_coords.txt | sed -e 's/ /_/g');
#			arret=$(echo $line | cut -d'|' -f3 | sed -e 's/_/ /g');
#			echo "        this.lines.put(\"$arret\", \"$subline\");";
#		done;
#	done;
#done;

for line in $(grep ^Found stops_coords.txt | sed -e 's/ /_/g'); do
	arret=$(echo $line | cut -d'|' -f3 | sed -e 's/_/ /g');
	files=$(grep "$arret" stops.*.txt | cut -d':' -f1 | sed -e 's/^stops\.//g' -e 's/\.txt$//g')
	names=""
	for id in $files; do
		name=$(grep "(id=$id)" lines.txt | sed -e "s/Line(id=$id): //g" -e 's/name={.*} //g' -e 's/name={.*}$//g' -e "s/name='.*'//g" -e 's/number=//g' -e 's/;//g' -e 's/ | / /g' -e 's/ $//g')
		for n in $name; do
			names="$names $n"
		done;
	done;
	names=$(echo $names | sed -e 's/ /\n/g' | sort | uniq);
	echo -n "        l = new ArrayList<String>();";
	for name in $names; do
		echo -n " l.add(\"$name\");";
	done;
	echo " this.lines.put(\"$arret\", l);"
done;
