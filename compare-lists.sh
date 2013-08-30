#!/bin/sh

ARRETS=$(mktemp)
COORDS=$(mktemp)

sh $(dirname $0)/liste-arrets.sh > $ARRETS
sh $(dirname $0)/liste-coords.sh > $COORDS

diff -uw $ARRETS $COORDS

rm $ARRETS $COORDS
