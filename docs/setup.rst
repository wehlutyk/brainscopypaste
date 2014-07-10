.. _setup:

Setup
=====

You need to install a few packages to get up and running with the analyses. Once this is done, you will be able to run all the analyses used in the paper and will have access to tools to explore all its data. In particular, this means you will be able to reproduce all the figures in the paper.

We'll assume you're using a Debian/Ubuntu system from now on. If it's not the case, do this on a virtual machine with Debian/Ubuntu, or figure out yourself how to do it on your own system (be it OS X, Windows, or any other OS).

The installation breaks down into three steps:

#. Creation and configuration of the python environment
#. Installation of TreeTagger
#. Installation of the datasets used by the suite

.. note::

   This software was tested on Python 2.7 ONLY. Any other version might (and probably will) generate unexpected errors.

Now let's get started. If you haven't done so already, open a shell, clone the main repository and ``cd`` into it::

   git clone https://github.com/wehlutyk/brainscopypaste
   cd brainscopypaste


Creating the environment
------------------------

You need ``virtualenv`` (`documentation <http://www.virtualenv.org/en/latest/>`_), ``virtualenvwrapper`` (`documentation <http://virtualenvwrapper.readthedocs.org/en/latest/>`_), ``tk-dev`` and ``redis-server`` for the environment to run the suite. On Debian/Ubuntu you can do this by running the following commands in a shell::

   sudo apt-get install virtualenvwrapper  # For isolating python environments; pulls in virtualenv automatically
   sudo apt-get install redis-server       # A key-value store for data storage

You can then create a virtual environment where we'll install the dependencies::

   mkvirtualenv brainscopypaste


Quick environment setup on a 64-bit machine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you are using a 64-bit Linux OS with by luck the same dependency versions as I use, the binaries for all the environment are already included in the repository, in ``wheelhouse``. Just run::

   ./install_wheels.sh

which should last only a few seconds, and you're good to go. You can jump directly to :ref:`treetagger-installation`.


Environment setup from source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On any other architecture, you must install and build the dependencies from source. Run the following::

   pip install -r requirements_numpy.txt   # Required for the next line to work
   pip install -r requirements.txt         # Needs numpy to be completely installed

.. todo::

   Detail build dependencies (e.g. ``tk-dev`` for matplotlib, but also ``build-essentials``, ``python-dev``, the fortran toolchain, etc.)

.. note::

   All further shell commands are assumed to be running inside this new virtual environment. It is activated automatically after the ``mkvirtualenv brainscopypaste`` command, but you can activate it manually in a new shell by running ``workon brainscopypaste``.


.. _treetagger-installation:

Install TreeTagger
------------------

TreeTagger is used to extract POS tags and lemmas from sentences, and is therefore needed for all mining steps. Install it by running::

   ./install_treetagger.sh

.. note::

   TreeTagger isn't packaged for usual GNU/Linux distributions, and the above script will do the install locally for you. If you're running another OS, you'll have to adapt the script to download the proper executable. See http://www.ims.uni-stuttgart.de/projekte/corplex/TreeTagger/ for more information.


Download datasets
-----------------

The software suite uses the following datasets for mining and word feature extraction:

* `WordNet <http://wordnet.princeton.edu/>`_ data
* `CMU Pronunciation Dictionary <http://www.speech.cs.cmu.edu/cgi-bin/cmudict>`_ data
* `Free Association Norms <http://w3.usf.edu/FreeAssociation/Intro.html>`_
* `Age-of-Acquisition Norms <http://crr.ugent.be/archives/806>`_
* `MemeTracker <http://memetracker.org/>`_ dataset

You can install all of these in one go by running::

   ./install_datasets.sh

You need a good internet connection to complete this step since the MemeTracker dataset (the largest) is about 220MB.

.. note::

   Age-of-Acquisition Norms are in fact already included in the cloned repository, because they needed to be converted from ``xslx`` to ``csv`` format (which is a pain to do in Python).
