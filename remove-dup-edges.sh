#!/bin/bash
EDGEFILE=$1
[ -f $EDGEFILE ] || return 1
head -n1 $EDGEFILE > $EDGEFILE.tmp
tail -n+2 $EDGEFILE | sort | uniq >> $EDGEFILE.tmp
mv $EDGEFILE.tmp $EDGEFILE