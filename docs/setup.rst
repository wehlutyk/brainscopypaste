.. _setup:

Setup
=====

Setting up the environment for the analyses is a bit involved.

If by chance you know how to use `Docker <https://www.docker.com/>`_ (or are willing to `learn <https://docs.docker.com/engine/getstarted/>`_ -- it's super useful and pretty easy!), the easiest way around this really is to use the `prebuilt container <https://hub.docker.com/r/wehlutyk/brainscopypaste>`_ which has everything included.
To do so read the :ref:`setup_docker` section.

Otherwise, or if you want more control over the setup, go to the :ref:`setup_manual` section, which walks you through the full show.

Once you're done (either with Docker or with the manual setup), you have access to all the analysis tools.
Among other things, this lets you reproduce the figures in the paper.

.. _setup_docker:

Quick setup using Docker
------------------------

If you have Docker installed, just run::

   docker run -it wehlutyk/brainscopypaste bash

That command will download the complete container (which might take a while since it bundles all the necessary data) and start a session in the container.
You see a normal shell prompt, which looks like this::

   brainscopypaste@3651c3dbcc4d:/$

Keep a note of the hexadecimal number after the ``@`` sign (it will be different for you), we'll use it later on to restart this session.
It's the ID of your container instance.

Now, in that same shell, start the PostgreSQL server::

   sudo service postgresql start

Then, ``cd`` into the analysis' home directory and run anything you want from the :ref:`usage` section::

   cd /home/brainscopypaste
   brainscopypaste <any-analysis-command>
   # -> the container computes...
   brainscopypaste <another-analysis-command>
   # -> the container does more computing...

Once you're done, just type ``exit`` (or Ctrl-D) to quit as usual in a terminal.

To restart the same container next time (and not a new instance, which will not now about any analyses you may have run), use your last container's ID::

   docker start -i <instance-id>

(You can also find a more human-readable name associated to that container ID by running ``docker ps -a``.)

Now if you're not a fan of Docker, you want see the detailed environment to use it yourself, or for any other reason you want to manually set up the analysis environment, keep reading below.

.. _setup_manual:

Manual setup
------------

There are a few packages to install to get up and running.

We'll assume you're using a Debian/Ubuntu system from now on.
If it's not the case, do this on a virtual machine with Debian/Ubuntu, or figure out yourself how to do it on your own system (be it OS X, Windows, or any other OS).

The installation breaks down into 6 steps:

#. :ref:`setup_dependencies`
#. :ref:`setup_virtualenv`
#. :ref:`setup_database`
#. :ref:`setup_treetagger`
#. :ref:`setup_datasets`
#. :ref:`setup_tests`

.. note::

   This software was tested on Python 3.5 ONLY (which is what the docker container uses).
   Any other version might (and probably will) generate unexpected errors.

Now let's get started.

.. _setup_dependencies:

Install preliminary dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, there's a bunch of packages we're going to need: among them are `virtualenv <http://www.virtualenv.org/en/latest/>`_ and `virtualenvwrapper <http://virtualenvwrapper.readthedocs.org/en/latest/>`_ to isolate the environment, PostgreSQL for database handling, and some build-time dependencies.
To get all the necessary stuff in one fell swoop, run::

    sudo apt-get install virtualenv virtualenvwrapper \
        postgresql postgresql-server-dev pkg-config python3-dev \
        build-essential libfreetype6-dev libpng12-0 libpng12-dev tk-dev

Then close and reopen your terminal (this loads the virtualenvwrapper scripts at startup).

.. _setup_virtualenv:

Create and configure the environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now clone the main repository and ``cd`` into it::

   git clone https://github.com/wehlutyk/brainscopypaste
   cd brainscopypaste

Next, create a Python 3 virtual environment, and install the dependencies::

   # Create the virtual environment
   mkvirtualenv -p $(which python3) brainscopypaste

   # Install NumPy first, which is required for the second line to work
   pip install $(cat requirements.txt | grep "^numpy")
   pip install -r requirements.txt
   # Finally install the `brainscopypaste` command-line tool
   pip install --editable .

While these instructions should be pretty foolproof, installing some of the dependencies (notably Matplotlib) can be a bit complicated.
If you run into problems, look at the `Matplotlib <http://matplotlib.org/>`_ installation instructions.
Another solution is to use the `Anaconda <https://www.continuum.io/why-anaconda>`_ distribution (but you have to juggle with nested anaconda and virtualenv environments in that case).

.. note::

   All further shell commands are assumed to be running inside this new virtual environment.
   It is activated automatically after the ``mkvirtualenv`` command, but you can activate it manually in a new shell by running ``workon brainscopypaste``.

.. _setup_database:

Configure the database
^^^^^^^^^^^^^^^^^^^^^^

First, the default configuration for PostgreSQL on Ubuntu requires a password for users other than ``postgres`` to connect, so we're going to change that to make things simpler:
edit the ``/etc/postgresql/<postgres-version>/main/pg_hba.conf`` file (in my case, I run ``sudo nano /etc/postgresql/9.5/main/pg_hba.conf``), and find the following lines, usually at the end of the file::

   # "local" is for Unix domain socket connections only
   local   all             all                                     peer
   # IPv4 local connections:
   host    all             all             127.0.0.1/32            md5
   # IPv6 local connections:
   host    all             all             ::1/128                 md5

Change the last column of those three lines to ``trust``, so they look like this::

   # "local" is for Unix domain socket connections only
   local   all             all                                     trust
   # IPv4 local connections:
   host    all             all             127.0.0.1/32            trust
   # IPv6 local connections:
   host    all             all             ::1/128                 trust

This configures PostgreSQL so that any user in the local system can connect as any database user.
Then, restart the database service to apply the changes::

   sudo service postgresql restart

Finally, create the user and databases used by the toolchain::

   psql -c 'create user brainscopypaste;' -U postgres
   psql -c 'create database brainscopypaste;' -U postgres
   psql -c 'alter database brainscopypaste owner to brainscopypaste;' -U postgres
   psql -c 'create database brainscopypaste_test;' -U postgres
   psql -c 'alter database brainscopypaste_test owner to brainscopypaste;' -U postgres

.. note::

   If you'd rather keep passwords for your local connections, then set a password for the ``brainscopypaste`` database user we just created, and put that password in the ``DB_PASSWORD`` variable of the *Database credentials* section of ``brainscopypaste/settings.py``.

.. _setup_treetagger:

Install TreeTagger
^^^^^^^^^^^^^^^^^^

`TreeTagger <http://www.ims.uni-stuttgart.de/projekte/corplex/TreeTagger/>`_ is used to extract POS tags and lemmas from sentences, so is needed for all mining steps.
Install it by running::

   ./install_treetagger.sh

.. note::

   TreeTagger isn't packaged for usual GNU/Linux distributions, and the above script will do the install locally for you.
   If you're running another OS, you'll have to adapt the script to download the proper executable.
   See the `project website <http://www.ims.uni-stuttgart.de/projekte/corplex/TreeTagger/>`_ for more information.

.. _setup_datasets:

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

.. _setup_tests:

Check everything works
^^^^^^^^^^^^^^^^^^^^^^

The toolchain has an extensive test suite, which you should now be able to run.
Still in the main repository with the virtual environment activated, run::

   py.test

This should take about 5-10 minutes to complete (it will skip a few tests since we haven't computed all necessary features yet).

If you run into problems, say some tests are failing, try first rerunning the test suite (the language detection module introduces a little randomness, leading a few tests to fail sometimes), then double check all the instructions above to make sure you followed them well.
If the problem persists please `create an issue <https://github.com/wehlutyk/brainscopypaste-paper/issues/new>`_ on the repository's bugtracker, because you may have found a bug!

If everything works, congrats!
You're good to go to the next section: :ref:`usage`.
