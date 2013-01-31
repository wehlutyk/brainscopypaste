# WebQuotes

Analyzing mutation in quotes when they propagate through the blog- and news-spaces. This should tell us stuff on how the brain copy-pastes and alters quotes when doing so.

This software was developed for a research paper based on the [MemeTracker](http://memetracker.org/) quotes database [to be pusblished]. It is released under the GNU/GPLv3 licence.


## Quickstart

Setup and usage of the software is a well-documented (though slightly intricate) process. The included docs explain it all, so here are the steps to build those docs on a Debian/Ubuntu system. In a shell, from the root directory of this repository, run the following:

    sudo apt-get install virtualenvwrapper   # For isolating python environments; pulls in virtualenv automatically
    sudo apt-get install tk-dev              # Needed to install matplotlib with TkAgg
    sudo apt-get install redis-server        # A key-value store for data storage; not necessary if you want only the docs
    mkvirtualenv webquotes
    pip install -r requirements_numpy.txt    # Required for the next line to work
    pip install -r requirements.txt          # Needs numpy to be completely installed
    cd docs
    make html

Then open the `docs/_build/html/index.html` file. It will walk you through all the steps to set up and use the software.
