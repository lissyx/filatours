#!/bin/bash

for line in $(grep ^Found stops_coords.txt | sed -e 's/ /_/g'); do
	arret=$(echo $line | cut -d'|' -f3 | sed -e 's/_/ /g');
	files=$(grep "$arret" stops.*.txt | cut -d':' -f1 | sed -e 's/^stops\.//g' -e 's/\.txt$//g')
	lineids=$(grep "$arret" stops.*.txt | cut -d'[' -f2 | cut -d']' -f1)
	names=""
	for lid in $lineids; do
		id=$(echo $lid | sed -e 's/A//g' -e 's/B//g')
		if [ -f stops.$id.txt ]; then
			name=$(grep "(id=$id)" lines.txt | sed -e "s/Line(id=$id): //g" -e 's/name={.*} //g' -e 's/name={.*}$//g' -e "s/name='.*'//g" -e 's/number=//g' -e 's/;//g' -e 's/ | / /g' -e 's/ $//g')
			echo $name | egrep -q '.+A|.+B'
			if [ $? -eq 0 ]; then
				#echo "lid=$lid ;; name==$name"
				finalname=$name
				#for na in $name; do
					#res=$(echo $na | sed -e "s/$name//g")
					#echo "$na -- $res"
					#if [ "$res" = "0" ]; then
					#	echo "lid=$lid ;; na==$na ==> $res"
					#	finalname=$na
					#fi
				#done;
			else
				finalname=$(echo $name | sed -e 's/ /_/g')
			fi;
		fi
		names="$names $finalname"
	done;
	names=$(echo $names | sed -e 's/ /\n/g' | sort | uniq);
	echo -n "        l = new ArrayList<String>();";
	for name in $names; do
		name=$(echo $name | sed -e 's/_/ /g')
		echo -n " l.add(\"$name\");";
	done;
	echo " this.lines.put(\"$arret\", l);"
done;
