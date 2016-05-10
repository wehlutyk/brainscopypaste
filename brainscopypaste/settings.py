from os.path import abspath, join


# All final settings should be in uppercase, the rest is ignored.

# MemeTracker filtering settings.
MT_FILTER_MIN_TOKENS = 5
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

# Notebook variant with a specific substitution-detection model.
NOTEBOOK = join(notebooks_root, '{model} - {notebook}')

# NLTK-builtin stopwords are a bit shallow, so we use these instead.
STOPWORDS = join(data_root, 'stopwords.txt')

# Age-of-Acquisition feature.
AOA = join(aoa_root, 'Kuperman-BRM-data-2012.csv')

# Clearpond-based features.
CLEARPOND = join(clearpond_root, 'englishCPdatabase2.txt')

# FreeAssociation-based features.
FA_SOURCES = [join(fa_root, fa) for
              fa in ['Cue_Target_Pairs.A-B',
                     'Cue_Target_Pairs.C',
                     'Cue_Target_Pairs.D-F',
                     'Cue_Target_Pairs.G-K',
                     'Cue_Target_Pairs.L-O',
                     'Cue_Target_Pairs.P-R',
                     'Cue_Target_Pairs.S',
                     'Cue_Target_Pairs.T-Z']]
PAGERANK = join(fa_root, 'pagerank.pickle')
BETWEENNESS = join(fa_root, 'betweenness.pickle')
CLUSTERING = join(fa_root, 'clustering.pickle')
DEGREE = join(fa_root, 'degree.pickle')

# MemeTracker data and features.
MT_SOURCE = join(mt_root, 'clust-qt08080902w3mfq5.txt')
MT_LENGTH = 8357595
FREQUENCY = join(mt_root, 'frequency.pickle')
TOKENS = join(mt_root, 'tokens.pickle')

# Where figures from notebooks live.
FIGURE = join(figures_root, '{}.png')
FIGURE_VARIANTS = join(figures_root, '{}')

# TreeTagger library folder.
TREETAGGER_TAGDIR = 'treetagger'
