"""Tag and tokenize strings using TreeTagger.

All the functions in this module are :func:`~.utils.memoized`, because they are
called very often and repeatedly.

"""


from treetaggerwrapper import TreeTagger, TreeTaggerError
from brainscopypaste.utils import find_parent_rel_dir, NotFoundError, memoized

from brainscopypaste.conf import settings


try:
    _treetagger = TreeTagger(
        TAGLANG='en', TAGPARFILE='english-utf8.par',
        TAGDIR=find_parent_rel_dir(settings.TREETAGGER_TAGDIR))
except NotFoundError:
    raise TreeTaggerError('TreeTagger directory not found '
                          '(searched parent directories '
                          'recursively)')


@memoized
def tag(sentence):
    """Get all the TreeTagger codings of `sentence` (tokens, POS tags,
    lemmas).

    Prefer using :func:`tags`, :func:`tokens`, or :func:`lemmas` which parse
    this function's output for you.

    """

    return tuple(t.split('\t') for t in
                 _treetagger.tag_text(sentence, notagdns=True))


@memoized
def tags(sentence):
    """Get the list of TreeTagger POS tags of `sentence`."""

    return tuple(t[1] for t in tag(sentence))


@memoized
def tokens(sentence):
    """Get the list of tokens of `sentence`."""

    return tuple(t[0].lower() for t in tag(sentence))


@memoized
def lemmas(sentence):
    """Get the list of lemmas of `sentence`."""

    return tuple(t[2].lower() for t in tag(sentence))
