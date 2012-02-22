#!/bin/bash
# Takes an XML file from Spinn3r, strips all namespaces (since they are
# usually undeclared, and invalidate the XML markup), and adds bounding
# <dataset> and </dataset> tags to the beginning and end of the file.

# Namespaces to be stripped
NAMESPACES="dc weblog atom post feed source"

# Check for the right number of arguments
if [ ! $# = 1 ]
then
    echo "Usage: `basename $0` xmlfile-to-strip"
    echo "Strips all namespaces from a Spinn3r XML file,"
    echo "and (hopefully) makes it valid XML."
    echo "Don't use any sapces in filenames!"
    exit 0
fi

# Prepare files
echo "Stripping the following namespaces from XML file:"
echo "    "$NAMESPACES
tmp1=$(tempfile)
tmp2=$(tempfile)
finalfile=${1%.*}.stripped.xml
cp $1 $tmp1

# Do the stripping
for ns in $NAMESPACES
do
    cat $tmp1 | sed "s/<${ns}:/</g" | sed "s/<\/${ns}:/<\//g" > $tmp2
    cp $tmp2 $tmp1
done

# Copy back and add the <dataset> and </dataset> tags
echo "<dataset>" > $finalfile
cat $tmp2 >> $finalfile
echo "</dataset>" >> $finalfile

# Clean up
rm $tmp1
rm $tmp2

echo "OK."
