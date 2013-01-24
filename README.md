WebQuotes
=========

Analyzing mutation in quotes when they propagate through the blogosphere. This should tell us stuff on how the brain behaves.

More to be added :-).


Installation
------------

This software is tested with Python 2.7 ONLY.

On Debian/Ubuntu, install a few required packages:

    sudo apt-get install virtualenvwrapper  # Useful for isolating python environments
    sudo apt-get install tk-dev             # Needed to compile matplotlib with TkAgg

TBD: any additional packages?
TBD: add some script to download nltk data and install treetagger.

Finally, create a virtualenv and install Python dependencies:

    mkvirtualenv webquotes
    pip install -r requirements_numpy.txt   # Used in the next line
    pip install -r requirements.txt         # Needs numpy to be completely installed
