Installation
============


Creating the environment
------------------------

You'll need ``virtualenv``, ``virtualenvwrapper``, ``tk-dev`` and ``redis-server`` for the environment to run the suite. On Debian/Ubuntu you can do this by running the following commands in a shell::

   sudo apt-get install virtualenvwrapper  # For isolating python environments; pulls in virtualenv
   sudo apt-get install tk-dev             # Needed to install matplotlib with TkAgg
   sudo apt-get install redis-server       # A key-value store for data storage


Then you can create a virtual environment and install the python dependencies::

   mkvirtualenv webquotes
   pip install -r requirements_numpy.txt   # Used in the next line
   pip install -r requirements.txt         # Needs numpy to be completely installed


All further shell commands are assumed to be running inside this new virtual environment. (You can activate that environment with ``workon webquotes``.)

The ``-u`` option used below with the python interpreter is to have unbuffered output: otherwise you'll get the information text messages only once the computations are over, not as it goes.


Other required dependencies
---------------------------

TBD: this should go in an automatic install script.

Install TreeTagger. Set paths in ``settings.py``.
