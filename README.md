# WebQuotes

Analyzing mutation in quotes when they propagate through the blog- and news-spaces. This should tell us stuff on how the brain copy-pastes and alters quotes when doing so.

This software was developed for a research paper based on the MemeTracker.org quotes database. [To be published]


## Installation

Please note that I tested this on Python 2.7 ONLY.


### Creating the environment

You'll need `virtualenv`, `virtualenvwrapper`, `tk-dev` and `redis-server` for the environment to run the suite. On Debian/Ubuntu you can do this by running the following commands in a shell:

    sudo apt-get install virtualenvwrapper  # For isolating python environments; pulls in virtualenv
    sudo apt-get install tk-dev             # Needed to install matplotlib with TkAgg
    sudo apt-get install redis-server       # A key-value store for data storage


Then you can create a virtual environment and install the python dependencies:

    mkvirtualenv webquotes
    pip install -r requirements_numpy.txt   # Used in the next line
    pip install -r requirements.txt         # Needs numpy to be completely installed


All further shell commands are assumed to be running inside this new virtual environment. (You can activate that environment with `workon webquotes.)

The `-u` option used below with the python interpreter is to have unbuffered output: otherwise you'll get the information text messages only once the computations are over, not as it goes.


### Other required dependencies

TBD: this should go in an automatic install script.

Download NLTK data for WordNet and the CMU Pronunciation Dictionary. Install TreeTagger. Set paths in `settings.py`.


## Usage

It boils down to five big steps.


### 1. Download the datasets

TBD: put this in a script
* MemeTracker
* Free Association Norms
* Age-of-Acquisition Norms


### 2. Preprocess the MemeTracker data

This reads the MemeTracker clusters file and imports various filtered versions of the clusters into a usable python datastructure, stored in Redis.

    sudo service redis-server start             # Start redis server
    python -u load_mt_clusters_to_pickle.py     # Filter clusters and save to pickle files
    python -u load_mt_pickle_to_redis.py        # Load the filtered clusters to Redis

You can get some preliminary statistics on the data by running the following:

    python 


### 3. Run substitution mining

This step finds substitutions according to the different substitution-detection models implemented. Careful that these commands are multiprocesssed, and will use all your CPUs minus one, so that I/O doesn't block.

`mine_substitutions.py` will mine with one given set of arguments defining a model. `mine_substitutions_multiple.py` will mine with multiple sets of arguments, testing all correct combinations of the lists of arguments you provide. So to mine with all imaginable models:

    python -u mine_substitutions_multiple.py \
        --ffs full framed filtered ff \                         # All filtered versions of clusters
        --models tbgs slidetbgs growtbgs time cumtbgs root \    # All detection models
        --substringss 0 1 \                                     # Include or don't include substitutions on substrings
        --POS a n v r all \                                     # All filters on POS tags
        --n_timebags 2 3 4 5 \                                  # Various slicings of clusters into timebags

Careful, the command above took about a day to complete on a 48-CPU / 500G-RAM workserver! You might want to try only a subset of those arguments.


### 4. Compute word features

To measure what happens during a substition (the ones you just mined), you need to characterize the way words are changed upon substitution. This step computes the features used to characterize substitutions.

TBD: add a link to the computed data for those who don't have a workstation to compute it all.


#### Age-of-Acquisition

    ## Compute features
    python -u load_aoa_Kuperman_to_pickle.py


#### CMU Pronunciation Dictionary

    ## Compute features
    python -u load_cmu_MNphonemes_to_pickle.py      # Mean numbers of phonemes
    python -u load_cmu_MNsyllables_to_pickle.py     # Mean numbers of syllables


#### Free Association Norms

    ## Preprocess norms data
    python -u load_fa_norms_to_pickle.py

    ## Compute features
    python -u load_fa_degrees_to_pickle.py          # Degrees of words
    python -u load_fa_CCs_to_pickle.py              # Clustering coefficients of words
    python -u load_fa_PageRank_to_pickle.py         # PageRank of words

    # /!\ laptop: 30 minutes
    python -u load_fa_BCs_to_pickle.py              # Betweenness centralities of words.

    # /!\ laptop: 30 minutes
    python -u load_fa_paths_to_pickle.py            # Path lengths distribution


Lines marked with a `/!\\` sign can be resource-demanding. The time indicated is an order of magnitude of the computing time with a 4x2.4GHz / 4G-RAM laptop.


#### WordNet

    ## Compute features
    python -u load_wn_degrees_to_pickle.py          # Degrees of words
    python -u load_wn_CCs_to_pickle.py              # Clustering coefficients of words

    # /!\ laptop: 2 hours
    python -u load_wn_PageRank_to_pickle.py         # PageRank of words

    # /!\ workserver: 20 hours
    python -u load_wn_BCs_to_pickle.py              # Betweenness centralities of words

    # /!\ workserver: 20 hours
    python -u load_wn_paths_to_pickle.py            # Path lengths distribution


Again, lines marked with a `/!\\` sign are pretty resource-demanding. the workserver used has 48 CPUs and 500G of RAM, and the last two lines used up to half the RAM.


### 5. Plot the results

You can now generate a (too) large number of graphs based on the mined data.

`analyze_substitutions.py` will let you see one graph for a set of arguments, and `analyze_substitutions_multiple.py` will build a series of graphs based on the argument sets you give it, combining them into all meaningful possibilities.


The graph outputs can be:

* Feature variation curves
* Feature susceptibilities
* Path lengths travelled upon substitution
* Position of substituted word in substituted quote


With all this you should be able to reproduce most of the figures in the paper [to be pusblished].
