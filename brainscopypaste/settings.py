"""Definition of the overall settings for the analysis.

Edit this module to permanently change settings for the analysis. Do NOT
directly import this module if you want to access these settings from inside
some other code; to do so see :data:`.conf.settings` (which also lets you
temporarily override settings).

All uppercase variables defined in this module are considered settings, the
rest is ignored.

See Also
--------
:class:`brainscopypaste.conf.Settings`

"""


from os.path import abspath, join


# MemeTracker filtering settings.
#: Minimum number of tokens a quote must have to be kept by the MemeTracker
#: filter.
MT_FILTER_MIN_TOKENS = 5
#: Maximum number of days a quote or a cluster can span to be kept by the
#: MemeTracker filter.
MT_FILTER_MAX_DAYS = 80

# Where all external and computed data lives.
data_root = abspath('data')
aoa_root = join(data_root, 'AoA')
clearpond_root = join(data_root, 'clearpond')
fa_root = join(data_root, 'FreeAssociation')
mt_root = join(data_root, 'MemeTracker')
figures_root = join(data_root, 'figures')
notebooks_root = join(data_root, 'notebooks')
# Paths to be created when settings are initialised.
paths_to_create = [data_root, aoa_root, fa_root, mt_root, figures_root,
                   notebooks_root]

#: Template for the file path to a notebook variant with a specific
#: substitution-detection model.
NOTEBOOK = join(notebooks_root, '{model} - {notebook}')

# NLTK-builtin stopwords are a bit shallow, so we use these instead.
#: Path to the file containing the list of stopwords.
STOPWORDS = join(data_root, 'stopwords.txt')

#: Path to the file containing word age of acquisition data.
AOA = join(aoa_root, 'Kuperman-BRM-data-2012.csv')

#: Path to the file containing word neighbourhood density data.
CLEARPOND = join(clearpond_root, 'englishCPdatabase2.txt')

#: List of files making up the Free Association data.
FA_SOURCES = [join(fa_root, fa) for
              fa in ['Cue_Target_Pairs.A-B',
                     'Cue_Target_Pairs.C',
                     'Cue_Target_Pairs.D-F',
                     'Cue_Target_Pairs.G-K',
                     'Cue_Target_Pairs.L-O',
                     'Cue_Target_Pairs.P-R',
                     'Cue_Target_Pairs.S',
                     'Cue_Target_Pairs.T-Z']]
#: Path to the pickle file containing word pagerank centrality values.
PAGERANK = join(fa_root, 'pagerank.pickle')
#: Path to the pickle file containing word betweeness centrality values.
BETWEENNESS = join(fa_root, 'betweenness.pickle')
#: Path to the pickle file containing word clustering coefficient values.
CLUSTERING = join(fa_root, 'clustering.pickle')
#: Path to the pickle file containing word degree centrality values.
DEGREE = join(fa_root, 'degree.pickle')

# MemeTracker data and features.
#: Path to the source MemeTracker data set.
MT_SOURCE = join(mt_root, 'clust-qt08080902w3mfq5.txt')
#: Number of lines in the :data:`MT_SOURCE` file (pre-computed with ``wc -l
#: <memetracker-file>``); used by :class:`~.load.MemeTrackerParser`.
MT_LENGTH = 8357595
#: Path to the pickle file containing word frequency values.
FREQUENCY = join(mt_root, 'frequency.pickle')
#: Path to the pickle file containing the list of known tokens.
TOKENS = join(mt_root, 'tokens.pickle')

# Where figures from notebooks live.
#: Template for the file path to a figure from the main analysis that is to be
#: saved.
FIGURE = join(figures_root, '{}.png')
#: Template for the folder containing all the figures of a notebook variant
#: with a specific substitution-detection model.
FIGURE_VARIANTS = join(figures_root, '{notebook}', '{model}')

#: TreeTagger library folder.
TREETAGGER_TAGDIR = 'treetagger'

# Database credentials.
#: PostgreSQL connection user name.
DB_USER = 'brainscopypaste'
#: PostgreSQL connection user password.
DB_PASSWORD = ''
#: Name of the PostgreSQL database used to store analysis data.
DB_NAME = 'brainscopypaste'
#: Name of the PostgreSQL database used to store test data.
DB_NAME_TEST = 'brainscopypaste_test'
