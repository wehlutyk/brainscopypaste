Root Scripts
============


Scripts for loading data and precomputing features
--------------------------------------------------


Parse, load, and filter MemeTracker data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``load_mt_clusters_to_pickle.py``

.. automodule:: load_mt_clusters_to_pickle

----

``load_mt_pickle_to_redis.py``

.. automodule:: load_mt_pickle_to_redis


Precompute classical linguistical features on words
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``load_mt_frequencies_to_pickle.py``

.. automodule:: load_mt_frequencies_to_pickle

----

``load_aoa_kuperman_to_pickle.py``

.. automodule:: load_aoa_Kuperman_to_pickle

----

``load_cmu_mnphonemes_to_pickle.py``

.. automodule:: load_cmu_MNphonemes_to_pickle

----

``load_cmu_mnsyllables_to_pickle.py``

.. automodule:: load_cmu_MNsyllables_to_pickle


Precompute Free Association-related features on words
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``load_fa_norms_to_pickle.py``

.. automodule:: load_fa_norms_to_pickle

----

``load_fa_BCs_to_pickle.py``

.. automodule:: load_fa_BCs_to_pickle

----

``load_fa_CCs_to_pickle.py``

.. automodule:: load_fa_CCs_to_pickle

----

``load_fa_degrees_to_pickle.py``

.. automodule:: load_fa_degrees_to_pickle

----

``load_fa_PageRank_to_pickle.py``

.. automodule:: load_fa_PageRank_to_pickle

----

``load_fa_paths_to_pickle.py``

.. automodule:: load_fa_paths_to_pickle


Precompute WordNet-related features on words
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``load_wn_BCs_to_pickle.py``

.. automodule:: load_wn_BCs_to_pickle

----

``load_wn_CCs_to_pickle.py``

.. automodule:: load_wn_CCs_to_pickle

----

``load_wn_NSigns_to_pickle.py``

.. automodule:: load_wn_NSigns_to_pickle

----

``load_wn_MNSyns_to_pickle.py``

.. automodule:: load_wn_MNSyns_to_pickle

----

``load_wn_degrees_to_pickle.py``

.. automodule:: load_wn_degrees_to_pickle

----

``load_wn_PageRank_to_pickle.py``

.. automodule:: load_wn_PageRank_to_pickle

----

``load_wn_paths_to_pickle.py``

.. automodule:: load_wn_paths_to_pickle


Scripts for mining substitutions and statistics
-----------------------------------------------

``mine_substitutions.py``

.. automodule:: mine_substitutions

----

``mine_substitutions_multiple.py``

.. automodule:: mine_substitutions_multiple

----

``mine_statistics.py``

.. automodule:: mine_statistics


Scripts for analyzing mined substitutions
-----------------------------------------

``analyze_substitutions.py``

.. automodule:: analyze_substitutions

----

``analyze_substitutions_multiple.py``

.. automodule:: analyze_substitutions_multiple


Further analyses
----------------

Finally, there are a few `IPython Notebook <http://www.ipython.org/notebook.html>`_\ s used to do some less generic analyses:

``feature_correlations.ipynb``

Compute the correlations between features on words.

----

``long_paths.ipynb``

Examine the substitutions where espcially long paths are travelled on the Free Association or WordNet networks.
