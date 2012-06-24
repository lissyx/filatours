#!/bin/sh

for line in $(python filbleu.py --list-lines | sed -e 's/ /_/g' | cut -d')' -f1 | cut -d'(' -f2 | grep ^id= | cut -d'=' -f2 | sort -n); do
	echo "Line $line";
	python filbleu.py --list-stops $line > stops.$line.txt;
done;
