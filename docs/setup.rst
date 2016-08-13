.. _setup:

Setup
=====

Quick setup using Docker
------------------------

Setting up the environment for the analyses is a bit involved.
If by chance you know how to use `Docker <https://www.docker.com/>`_ (or are willing to `learn <https://docs.docker.com/engine/getstarted/>`_ -- it's super useful and pretty easy!), the easiest way around this really is to use the `prebuilt container <https://hub.docker.com/r/wehlutyk/brainscopypaste>`_ which has everything included.
Just like the manual setup (further down), it gives you access to all the analysis tools.
Among other things, this lets you reproduce the figures in the paper.
So if you have Docker installed, just run::

   docker run wehlutyk/brainscopypaste

That command will download the complete container (which might take a while since it bundles all the necessary data) and run the general command-line tool.
With that you can jump straight to the :ref:`usage` section, and you just need to replace all instances of::

   brainscopypaste [arguments]

with::

   docker run wehlutyk/brainscopypaste [arguments]

If you're not a fan of Docker, you want see the detailed environment to use it yourself, or for any other reason you want to manually set up the analysis environment, keep reading below.

Manual setup
------------

There are a few packages to install to get up and running.

We'll assume you're using a Debian/Ubuntu system from now on.
If it's not the case, do this on a virtual machine with Debian/Ubuntu, or figure out yourself how to do it on your own system (be it OS X, Windows, or any other OS).

The installation breaks down into four steps:

#. Install preliminary dependencies
#. Create and configure the python environment
#. Install TreeTagger
#. Install the datasets used in the analyses

.. note::

   This software was tested on Python 3.5 ONLY (which is what the docker container uses). Any other version might (and probably will) generate unexpected errors.

Now let's get started.

Install dependencies
^^^^^^^^^^^^^^^^^^^^

First, there's a bunch of packages we're going to need: among them are `virtualenv <http://www.virtualenv.org/en/latest/>`_ and `virtualenvwrapper <http://virtualenvwrapper.readthedocs.org/en/latest/>`_ to isolate the environment, PostgreSQL for database handling, and some build-time dependencies.
To get all the necessary stuff in one fell swoop, run::

    sudo apt-get install virtualenv virtualenvwrapper \
        postgresql postgresql-server-dev pkg-config python3-dev \
        build-essential libfreetype6-dev libpng12-0 libpng12-dev tk-dev

Then close and reopen your terminal (this loads the virtualenvwrapper scripts at startup).

Create and configure the environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now clone the main repository and ``cd`` into it::

   git clone https://github.com/wehlutyk/brainscopypaste
   cd brainscopypaste

Next, create a Python 3 virtual environment, and install the dependencies::

   # Create the virtual environment
   mkvirtualenv -p $(which python3) brainscopypaste

   # Install NumPy first, which is required for the next line to work
   pip install $(cat requirements.txt | grep "^numpy")
   pip install -r requirements.txt
   # Finally install the `brainscopypaste` command-line tool
   pip install --editable .

While these instructions should be pretty foolproof, installing some of dependencies (notably Matplotlib) can be a bit complicated.
If you run into problems, look at the Matplotlib installation instructions.
Another solution is to use the `Anaconda <https://www.continuum.io/why-anaconda>`_ distribution (but you have to juggle with nested environments in that case).

.. note::

   All further shell commands are assumed to be running inside this new virtual environment. It is activated automatically after the ``mkvirtualenv brainscopypaste`` command, but you can activate it manually in a new shell by running ``workon brainscopypaste``.

.. _treetagger-installation:

Install TreeTagger
^^^^^^^^^^^^^^^^^^

TreeTagger is used to extract POS tags and lemmas from sentences, so is needed for all mining steps.
Install it by running::

   ./install_treetagger.sh

.. note::

   TreeTagger isn't packaged for usual GNU/Linux distributions, and the above script will do the install locally for you.
   If you're running another OS, you'll have to adapt the script to download the proper executable.
   See http://www.ims.uni-stuttgart.de/projekte/corplex/TreeTagger/ for more information.

Install datasets
^^^^^^^^^^^^^^^^

The analyses use the following datasets for mining and word feature extraction:

* `WordNet <http://wordnet.princeton.edu/>`_ data
* `CMU Pronunciation Dictionary <http://www.speech.cs.cmu.edu/cgi-bin/cmudict>`_ data
* `Free Association Norms <http://w3.usf.edu/FreeAssociation/Intro.html>`_
* `Age-of-Acquisition Norms <http://crr.ugent.be/archives/806>`_
* `CLEARPOND <http://clearpond.northwestern.edu>`_ data
* `MemeTracker <http://memetracker.org/>`_ dataset

You can install all of these in one go by running::

   ./install_datasets.sh

.. note::

   Age-of-Acquisition Norms are in fact already included in the cloned repository, because they needed to be converted from ``xslx`` to ``csv`` format (which is a pain to do in Python).
