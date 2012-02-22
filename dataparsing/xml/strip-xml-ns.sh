#!/bin/bash

NAMESPACES="dc weblog atom post feed source"

if [ ! $# = 1 ]
then
    echo "Usage: `basename $0` xmlfile-to-strip"
    echo "Strips all namespaces from a Spinn3r XML file,"
    echo "and (hopefully) makes it valid XML."
    echo "Don't use any sapces in filenames!"
    exit 0
fi

echo "Stripping the following namespaces from XML file:"
echo "    "$NAMESPACES
tmp1=$(tempfile)
tmp2=$(tempfile)
finalfile=${1%.*}.stripped.xml
cp $1 $tmp1

for ns in $NAMESPACES
do
    cat $tmp1 | sed "s/<${ns}:/</g" | sed "s/<\/${ns}:/<\//g" > $tmp2
    cp $tmp2 $tmp1
done

echo "<dataset>" > $finalfile
cat $tmp2 >> $finalfile
echo "</dataset>" >> $finalfile
rm $tmp1
rm $tmp2

echo "OK."
