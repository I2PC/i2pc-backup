#!/bin/bash

#cp $1 $1.old
T=`mktemp`
cat $1 | while read module directories
do
	echo $module 1 $directories >> $T
done
mv $T $1
