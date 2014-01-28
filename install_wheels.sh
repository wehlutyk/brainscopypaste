#!/bin/bash
# Install local wheels to a virtual environment,
# making sure any git-based package is still taken from the wheels,
# not from its source repo.

echo "*** Installing wheels ***"
BASEDIR=$(dirname $0)
WHEELSDIR="${BASEDIR}/wheelhouse-x86_64"
ls "${WHEELSDIR}"/*.whl $1 | while read x
do
    pip install --use-wheel --no-index --find-links="${WHEELSDIR}" $x
done

echo
echo "*** Installing MathJax for IPython Notebook ***"
python -m IPython.external.mathjax
