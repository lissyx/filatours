#!/bin/sh

ARRETS=$(mktemp)
COORDS=$(mktemp)
DIFFTOOL=${DIFFTOOL:-"diff -uw"}

sh $(dirname $0)/liste-arrets.sh > $ARRETS
sh $(dirname $0)/liste-coords.sh > $COORDS

${DIFFTOOL} $ARRETS $COORDS

rm $ARRETS $COORDS
