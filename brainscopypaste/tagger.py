"""Tag and tokenize sentences and quotes."""


from treetaggerwrapper import TreeTagger, TreeTaggerError
from brainscopypaste.utils import find_parent_rel_dir, NotFoundError, memoized

from brainscopypaste import paths


try:
    _treetagger = TreeTagger(
        TAGLANG='en', TAGPARFILE='english.par',
        TAGDIR=find_parent_rel_dir(paths.treetagger_TAGDIR))
except NotFoundError:
    raise TreeTaggerError('TreeTagger directory not found '
                          '(searched parent directories '
                          'recursively)')


@memoized
def tag(sentence):
    """Tag a sentence."""
    return [t.split('\t')
            for t in _treetagger.tag_text(sentence, notagdns=True)]


def tags(sentence):
    """Get the tags of a sentence."""
    return [t[1] for t in tag(sentence)]


def tokens(sentence):
    """Get the tokens of a sentence."""
    return [t[0] for t in tag(sentence)]


def lemmas(sentence):
    """Get the lemmas of a sentence."""
    # TODO: test relemmatizing with wordnet here (will apply everywhere)
    return [t[2] for t in tag(sentence)]
