.. _usage:

Usage
=====

In the previous section we set up the environment, installed the dependencies, and downloaded the datasets. Those datasets divide in two categories:

* The MemeTracker dataset, which contains all the blog and quotes data
* All the other datasets, which are used to compute word features

The general flow for the analysis is as follows:

#. Filter through all of the MemeTracker data looking for substitutions from one quote to another. This is not a trivial task, since substitutions are not directly available from the dataset (because it contains no ``source -> destination`` information) and thus have to be detected based on various models that imagine how the substitution process takes place. Call this step **substitution mining** . The output of this step is a list of mined substitutions; and since we have several ways of mining those substitutions, we obtain a list of mined substitutions for each mining method (or *argument set*). *This step accounts for about half of the total computation time of the final results.*
#. To characterize the way words are modified upon substitution we compute a set of features for each word, which we use in the next step by examining how those features vary when a word is substituted. Call this step **word feature computation**. *This step accounts for the other half of the computation time of the final results.*
#. We now have lists of substitutions (one for each mining method) and a set of features for the words involved in the substitutions ; it's time to plot the variations of those features upon substitution. This is the final exploratory step, which we can call **substitution visualization**.

Now let's get all this running!


Preprocess the MemeTracker data
-------------------------------

The MemeTracker data comes in a text-based format, which isn't quite suitable for the analysis we want to perform. Before diving into substitution mining, we need to parse the dataset to store it in better-suited python objects. All these objects will be stored in the Redis backend (this speeds up program loading and lets multiple processes read the data without needing to copy it several times in memory).

The following commands will read the MemeTracker clusters file and import various filtered versions of the clusters into usable python datastructures, stored in Redis::

   sudo service redis-server start             # Start redis server
   python -u load_mt_clusters_to_pickle.py     # Filter clusters and save to pickle files
   python -u load_mt_pickle_to_redis.py        # Load the filtered clusters to Redis

The data that was loaded to Redis is also stored in files in pickle format, located at ``data/MemeTracker/clust-qt08080902w3mfq5.txt*.pickle``.

You can already get some preliminary statistics on the data by running the following::

   python -u mine_statistics.py

.. note::

   For most graphing, you will also need to install a working LaTeX distribution since text rendering is done through LaTeX. On Arch, ``sudo pacman -S texlive-core texlive-latexextra`` does the trick. Alternatively, you can comment out line 154 of the ``matplotlibrc`` file at the root of this repository, which will disable LaTeX rendering.


Run substitution mining
-----------------------

You can now start the actual substitution mining. ``mine_substitutions.py`` will mine with one given set of arguments defining a model, and ``mine_substitutions_multiple.py`` will mine with multiple sets of arguments, testing all correct combinations of the lists of arguments you provide. The arguments for those commands fall into two types (the plurals, denoted by ``[s]``, are for ``mine_substitutions_multiple.py``):

* On one side:

  * ``--ff[s]``: selects which filtered version of the MemeTracker clusters to work on

* On the other side:

  * ``--model[s]``: selects which substitution detection model to use (see the paper's supplementary data [LeriqueRoth12suppl]_ and the :ref:`reference` documentation for more details)
  * ``--substrings[s]``: indicates whether or not to include susbtitutions of substrings of quotes
  * ``--POS[s]``: selects which kind of filtering is applied using the POS tags of the words (see the paper's supplementary data [LeriqueRoth12suppl]_ and the :ref:`reference` documentation for more details)
  * ``--timebag_size[s]``: selects the size (in days) of the timebags the clusters are sliced into, for substitution detection models that use slicing (i.e. ``tbgs``, ``cumtbgs``, ``slidetbgs`` and ``growtbgs``)

So to mine with all imaginable models, settings,  and filtered versions of the clusters::

   python -u mine_substitutions_multiple.py \
       --ffs full framed filtered ff \                         # All filtered versions of clusters
       --models tbgs cumtbgs slidetbgs growtbgs time root \    # All detection models
       --substringss 0 1 \                                     # Include or don't include substitutions on substrings
       --POSs a n v r all \                                    # All filters on POS tags
       --timebag_sizes 1 2 3                                   # Various slicings of clusters into timebags

.. note::

   These commands are multiprocesssed and will use all your CPUs minus one (so that I/O doesn't block) and a lot of RAM. As an example, the command above took about a day to complete on a 48-CPU / 500G-RAM workserver! You might want to try only a subset of those arguments.


Compute word features
---------------------

To measure what happens during a substitution (the ones you just mined), you need to characterize the way words are changed upon substitution. This step computes the features used to characterize substitutions.

.. todo::

   Add a link to the computed data for those who don't have a workstation to compute it all.


Word Frequencies
^^^^^^^^^^^^^^^^

Compute the word frequencies in the MemeTracker dataset, and save that to a pickle file::

   ## Compute word frequencies
   python -u load_mt_frequencies_to_pickle.py


Age-of-Acquisition
^^^^^^^^^^^^^^^^^^

Load the Age-of-Acquisition features to a usable pickle file::

   ## Load feature to pickle
   python -u load_aoa_Kuperman_to_pickle.py


CMU Pronunciation Dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Compute the Mean Number of Phonemes and the Mean Number of Syllables using NLTK / CMU, and save them to a usable pickle file::

   ## Compute features
   python -u load_cmu_MNphonemes_to_pickle.py      # Mean numbers of phonemes
   python -u load_cmu_MNsyllables_to_pickle.py     # Mean numbers of syllables


Free Association Norms
^^^^^^^^^^^^^^^^^^^^^^

Load Free Association Norms to a usable pickle file, and compute the four main features based on the norms as well as the path lengths distribution::

   ## Preprocess norms data
   python -u load_fa_norms_to_pickle.py

   ## Compute features
   python -u load_fa_degrees_to_pickle.py          # Degrees of words
   python -u load_fa_CCs_to_pickle.py              # Clustering coefficients of words
   python -u load_fa_PageRank_to_pickle.py         # PageRank of words

   # /!\ laptop: 30 minutes
   python -u load_fa_BCs_to_pickle.py              # Betweenness centralities of words

   # /!\ laptop: 30 minutes
   python -u load_fa_paths_to_pickle.py            # Path lengths distribution

.. note::

   Lines marked with a ``/!\`` sign can be resource-demanding. The time indicated is an order of magnitude of the computing time with a 4x2.4GHz / 4G-RAM laptop.


WordNet
^^^^^^^

Compute the four main features and path lengths distribution from the WordNet network::

   ## Compute features
   python -u load_wn_degrees_to_pickle.py          # Degrees of words
   python -u load_wn_CCs_to_pickle.py              # Clustering coefficients of words
   python -u load_wn_NSigns_to_pickle.py           # Number of meanings of words
   python -u load_wn_MNSyns_to_pickle.py           # Mean number of synonyms of words

   # /!\ laptop: 2 hours
   python -u load_wn_PageRank_to_pickle.py         # PageRank of words

   # /!\ workserver: 20 hours
   python -u load_wn_BCs_to_pickle.py              # Betweenness centralities of words

   # /!\ workserver: 20 hours
   python -u load_wn_paths_to_pickle.py            # Path lengths distribution

.. note::

   Again, lines marked with a ``/!\`` sign are pretty resource-demanding. The workserver used has 48 CPUs and 500G of RAM, and the last two commands used up to half the RAM.

.. todo::

   Of those features, only ``MNSyns`` is still used, so we can remove the rest from these instructions and save the computations.


Plot the results
----------------

You can now generate a (too) large number of graphs based on the mined data.

``analyze_substitutions.py`` will let you see one graph for a set of arguments, and ``analyze_substitutions_multiple.py`` will build a series of graphs based on the argument sets you give it, combining them into all meaningful possibilities.


The graph outputs can be:

* Feature variation curves
* Feature susceptibilities
* Path lengths travelled upon substitution
* Position of substituted word in substituted quote


With all this you should be able to reproduce most of the figures in the paper [to be pusblished].


References
----------

.. [LeriqueRoth12suppl] to be pusblished

.. todo::

   Add paper supplementary data reference
