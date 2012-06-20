#!/bin/sh

for line in $(python filbleu.py --list-lines | cut -d' ' -f3 | sed -e 's/\[//g' | sed -e 's/\]//g'); do
	echo "Line $line";
	python filbleu.py --list-stops $line > stops.$line.txt;
done;
