.. _usage:

Usage
=====

This section explains how to re-run the full analysis (including what is described in the paper).
The general flow for the analysis is as follows:

#. :ref:`usage_preload`, which consists of the following 3 steps:

   #. :ref:`usage_memetracker_load`
   #. :ref:`usage_memetracker_filter`
   #. :ref:`usage_features_load`

#. :ref:`usage_single_model`, which consists of the following 2 steps:

   #. :ref:`usage_mine`
   #. :ref:`usage_notebooks`

Once you did that for a particular substitution model, you can do the :ref:`usage_variants`.

Now let's get all this running!

.. _usage_preload:

Preload all necessary data
--------------------------

The first big part is to load and preprocess all the bits necessary for the analysis. Let's go:

.. _usage_memetracker_load:

Load the MemeTracker data into the database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MemeTracker data comes in a text-based format, which isn't suitable for the analysis we want to perform.
So the first thing we do is load it into a PostgreSQL database.
First, make sure the database service is running::

   sudo service postgresql start

Then, from inside the analysis' repository (with the virtual environment activated if you're not using Docker --- see the :ref:`setup` section if you're lost here), tell the toolchain to load the MemeTracker data into the database::

   brainscopypaste load memetracker

This might take a while to complete, as the MemeTracker data takes up about 1GB and needs to be processed for the database.
The command-line tool will inform you about its progress.

.. _usage_memetracker_filter:

Preprocess the MemeTracker data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now, the data we just loaded contains quite some noise.
Our next step is to filter out all the noise we can, to work on a cleaner data set overall.
To do so, run::

   brainscopypaste filter memetracker

This is also a bit long (but, as usual, informs you of the progress).

.. _usage_features_load:

Load and compute word features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The final preloading step is to compute the features we'll use on words involved in substitutions.
This comes after loading and filtering the MemeTracker data, since some features (like word frequency) are computed on the filtered MemeTracker data itself.
To load all the features, run::

   brainscopypaste load features

Now you're ready to mine substitutions and plot the results.

.. _usage_single_model:

Analyse substitutions mined by one model
----------------------------------------

So first, choose a substitution model (read the `paper <https://hal.archives-ouvertes.fr/hal-01143986/>`_ for more information on this).
If you want to use the model detailed in the paper, just follow the instructions below.

.. _usage_mine:

Mine for substitutions
^^^^^^^^^^^^^^^^^^^^^^

To mine for all the substitutions that the model presented in the paper detects, run::

   brainscopypaste mine substitutions Time.discrete Source.majority Past.last_bin Durl.all 1

This will iterate through the MemeTracker data, detect all substitutions that conform to the main model presented in the paper, and store them in the database.

Head over to the :ref:`reference_cli` reference for more details about what the arguments in this command mean.

.. _usage_notebooks:

Run the analysis notebooks
^^^^^^^^^^^^^^^^^^^^^^^^^^

Once substitutions are mined, results are obtained by running the Jupyter notebooks located in the ``notebooks/`` folder.
To do so, still in the same terminal, run::

   jupyter notebook

Which will open the Jupyter file browser in your web browser.

Then click on the ``notebooks/`` folder, and open any analysis notebook you want and run it.
All the figures presenting results in the paper come from these notebooks.

.. note::

   If you used another substitution model than the one used above, you must correct the corresponding ``model = Model(...)`` line in the ``distance.ipynb``, ``susceptibility.ipynb``, and ``variation.ipynb`` notebooks.

.. _usage_variants:

Analysis exploring all mining models
------------------------------------

Part of the robustness of the analysis comes from the fact that results are reproducible across substitution models.
To compute the results for all substitution models, you must first mine all the possible substitutions.
This can be done with the following command::

   for time in discrete continuous; do \
     for source in majority all; do \
       for past in last_bin all; do \
         for durl in all exclude_past; do \
           for maxdistance in 1 2; do \
             echo "\n-----\n\nDoing Time.$time Source.$source Past.$past Durl.$durl $maxdistance"; \
             brainscopypaste mine substitutions Time.$time Source.$source Past.$past Durl.$durl $maxdistance; \
           done; \
         done; \
       done; \
     done; \
   done;

(This will take a loooong time to complete.
The ``Time.continuous|discrete Source.all Past.all Durl.all 1|2`` models especially, will use a lot of RAM.)

Once substitutions are mined for all possible models (or a subset of those), you can run notebooks for each model directly in the command-line (i.e. without having to open each notebook in the browser) with the ``brainscopypaste variant <model-parameters> <notebook-file>`` command.
It will create a copy of the notebook you asked for, set the proper ``model = Model(...)`` line in it, run it and save it in the ``data/notebooks/`` folder.
All the figures produced by that notebook will also be saved in the ``data/figures/<model> - <notebook>/`` folder.

So to run the whole analysis for all models, after mining for all models, run::

   for time in discrete continuous; do \
     for source in majority all; do \
       for past in last_bin all; do \
         for durl in all exclude_past; do \
           for maxdistance in 1 2; do \
             echo "\n-----\n\nDoing Time.$time Source.$source Past.$past Durl.$durl $maxdistance"; \
             brainscopypaste variant Time.$time Source.$source Past.$past Durl.$durl $maxdistance notebooks/distance.ipynb; \
             brainscopypaste variant Time.$time Source.$source Past.$past Durl.$durl $maxdistance notebooks/susceptibility.ipynb; \
             brainscopypaste variant Time.$time Source.$source Past.$past Durl.$durl $maxdistance notebooks/variation.ipynb; \
           done; \
         done; \
       done; \
     done; \
   done;

Needless to say, this plus mining will take at least a couple days to complete.

If you want to know more to try and hack on the analysis on the notebooks, head over to the :ref:`reference`.
