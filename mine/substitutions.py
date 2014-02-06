#!/usr/bin/env python # -*- coding: utf-8 -*-

"""Analyze data from the MemeTracker dataset.

"""


from __future__ import division

from warnings import warn
from multiprocessing import cpu_count

import numpy as np

from linguistics.distance import levenshtein
from linguistics.treetagger import get_tagger
from linguistics.wn import lemmatize
import datainterface.picklesaver as ps
import datainterface.redistools as rt
import datainterface.fs as di_fs
from util.generic import ProgressInfo
from util.mp import LoggingPool
import settings as st


class Substitution(object):

    """Represent a substitution detected in the dataset, and provide useful
    methods on it.

    :class:`SubstitutionsMiner` creates instances of this class to be later
    saved directly in pickle files.

    Parameters
    ----------
    ma : :class:`~mine.args.MiningArgs`
        The mining args with which the substitution was found, and to be
        followed for future operations.
    mother : :class:`~datastructure.full.QtString`
        The source quote for the substitution.
    daughter : :class:`~datastructure.full.QtString`
        The destination quote for the substitution.
    mining_info : dict or None
        Additional information about the substitution as given by
        :meth:`~mine.models.ClusterModels.iter_substitutions` (it depends
        on the chosen source-destination model), for potential later use.

    Attributes
    ----------
    pos_wn_to_tt
    ma : :class:`~mine.args.MiningArgs`
        The mining args given to the constructor.
    mother : :class:`~datastructure.full.QtString`
        The mother quote given to the constructor.
    daughter : :class:`~datastructure.full.QtString`
        The daughter quote given to the constructor.
    mining_info : dict or None
        The additional mining information given to the constructor.
    qt_length : int
        Length of the mother and daughter quotes, in number of words (the
        mother and daughter are always the same size, even when mining
        includes substrings since what we see here is the effective mother).
    word1 : string
        The word that disappeared.
    word2 : string
        The word that appeared instead of `word1`.
    idx : int
        The position of `word1` in `mother` (which is also the position of
        `word2` in `daughter`).

    See Also
    --------
    SubstitutionsMiner

    """

    #: Correspondence between WordNet POS tags and TreeTagger POS tags.
    pos_wn_to_tt = {'a': 'J', 'n': 'N', 'v': 'V', 'r': 'R'}

    def __init__(self, ma, mother, daughter, mining_info):
        """Initialize the structure with substitution information.

        Once the attributes are initialized, information is printed to stdout
        (conditional on the provided mining args) and the words involved are
        lemmatized (but usage of that is also conditional on the mining args).

        Parameters
        ----------
        ma : :class:`~mine.args.MiningArgs`
            The mining args with which the substitution was found, and to be
            followed for future operations.
        mother : :class:`~datastructure.full.QtString`
            The source quote for the substitution.
        daughter : :class:`~datastructure.full.QtString`
            The destination quote for the substitution.
        mining_info : dict or None
            Additional information about the substitution as given by
            :meth:`~mine.models.ClusterModels.iter_substitutions` (it depends
            on the chosen source-destination model), for potential later use.

        """

        self.ma = ma
        self.mother = mother
        self.daughter = daughter
        self.idx = np.where([w1 != w2 for (w1, w2) in
                             zip(daughter.tokens, mother.tokens)])[0]
        self.qt_length = len(mother.tokens)
        self.word1 = mother.tokens[self.idx]
        self.word2 = daughter.tokens[self.idx]
        self.mining_info = mining_info
        self.print_info()
        self.lemmatize()

    def __getitem__(self, key):
        return self.__getattribute__(key)

    def lemmatize(self):
        """Lemmatize the words involved in the substitution and log that
        information if asked to.

        The lemmatized words are stored respectively in `self.lem1` and
        `self.lem2`, but are only used later if the mining args say so.

        """

        tagger = get_tagger()
        t1 = tagger.Lemmatize(self.mother)[self.idx]
        t2 = tagger.Lemmatize(self.daughter)[self.idx]

        self.lem1 = lemmatize(t1)
        self.lem2 = lemmatize(t2)

        if self.ma.verbose:
            print ("Lemmatized: '" + self.lem1 + "' -> '" +
                   self.lem2 + "'")

    def print_info(self):
        """Print information about the substitution if the mining
        args asks for it."""

        if self.ma.verbose:

            raw_input()
            print
            print ("***** SUBST (cl #{} / {}) ***** '".format(
                self.mother.cl_id, self.mining_info) +
                '{}/{}'.format(self.mother.tokens[self.idx],
                               self.mother.POS_tags[self.idx]) +
                "' -> '" +
                '{}/{}'.format(self.daughter.tokens[self.idx],
                               self.daughter.POS_tags[self.idx]) +
                "'")
            print self.mother
            print '=>'
            print self.daughter
            print

    def test_POS(self):
        """Test for correspondence of POS tags in the substitution.

        If the mining args ask for 'all' POS tags, we only check if the source
        and destination words have same POS tag (returning ``True`` or
        ``False``). If the mining args ask for a specific POS tag, we check
        that both source and destination words have that POS tag, and return
        ``False`` if not. In both cases, information is logged to stdout if the
        mining args ask for it.

        Returns
        -------
        bool
            ``True`` if the POS tags correspond to what the mining args ask
            for, ``False`` otherwise (see above for the detailed explanation).

        """

        ret = True

        if self.ma.POS == 'all':

            if self.daughter.POS_tags[self.idx][0] != \
                    self.mother.POS_tags[self.idx][0]:
                if self.ma.verbose:
                    print 'Not kept (different POS)'
                ret = False

        else:

            if (self.daughter.POS_tags[self.idx][0] !=
                    self.pos_wn_to_tt[self.ma.POS] or
                    self.mother.POS_tags[self.idx][0] !=
                    self.pos_wn_to_tt[self.ma.POS]):
                if self.ma.verbose:
                    print 'Not kept (wrong POS)'
                ret = False

        return ret

    def test_real(self):
        """Test if the source and destination words really form a substitution,
        or are in fact only variations of the same root.

        Many detected substitutions are in fact a plural form changing to a
        singular form, a minor grammatical conjugation change, or the like. We
        don't want to keep these, and this method lets us filter them most of
        those cases by rejecting the substitution if source and destination
        word only differ by a single edit (levenshtein-distance 1).

        Returns
        -------
        bool
            ``True`` if the substitution is considered to really be a
            substitution, ``False`` otherwise.

        """

        ret = True

        if levenshtein(self.lem1, self.lem2) <= 1:
            if self.ma.verbose:
                print 'Not kept (not substitution)'
            ret = False

        return ret


def instantiate_and_mine(ma):
    """Create a :class:`SubstitutionsMiner` instance and start its mining
    (used for multithreading).

    Parameters
    ----------
    ma : :class:`~mine.args.MiningArgs`
        The mining args to use.

    See Also
    --------
    SubstitutionsMiner

    """

    sm = SubstitutionsMiner(ma)
    sm.mine()


def mine_multiple(mma):
    """Mine sequentially for a series of mining arguments.

    Parameters
    ----------
    maa : :class:`~mine.args.MultipleMiningArgs`
        All the mining argument sets to be mined for.

    See Also
    --------
    SubstitutionsMiner

    """

    mma.print_mining()

    for ma in mma:
        instantiate_and_mine(ma)


def mine_multiple_mt(mma):
    """Mine for a series of mining arguments, multi-threading over the
    number of cores available minus one (so as not to block IO).

    Parameters
    ----------
    maa : :class:`~mine.args.MultipleMiningArgs`
        All the mining argument sets to be mined for.

    See Also
    --------
    SubstitutionsMiner

    """

    mma.print_mining()
    n_jobs = len(mma)

    n_cpu = cpu_count()
    n_proc = n_cpu - 1

    print
    print 'Using {} workers to do {} jobs.'.format(n_proc, n_jobs)

    pool = LoggingPool(processes=n_proc, maxtasksperchild=1)
    res = pool.map_async(instantiate_and_mine, mma)

    # The timeout here is to be able to keyboard-interrupt.
    # See http://bugs.python.org/issue8296 for details.

    res.wait(1e12)


class SubstitutionsMiner(object):

    def __init__(self, ma, start=False):
        self.ma = ma
        if start:
            self.mine()

    def load_clusters(self):
        """Load the data from pickle files.

        """

        print
        print 'Connecting to redis server for cluster data...',

        ff_dict = {'full': st.redis_mt_clusters_pref,
                   'framed': st.redis_mt_clusters_framed_pref,
                   'filtered': st.redis_mt_clusters_filtered_pref,
                   'ff': st.redis_mt_clusters_ff_pref}
        self.clusters = rt.RedisReader(ff_dict[self.ma.ff])

        print 'OK'

    def iter_substitutions(self):
        """Iterate through all substitutions according to the given
        MiningArgs."""
        progress = ProgressInfo(len(self.clusters), 100, 'clusters')

        for cl in self.clusters.itervalues():

            progress.next_step()
            for mother, daughter, mining_info in \
                    cl.iter_substitutions[self.ma.model](self.ma):
                yield (mother, daughter, mining_info)

    def examine_substitutions(self):
        """Examine substitutions and retain only those we want.

        Details: TODO

        """

        print
        print 'Mining substitutions:'

        # Results of the mining
        self.substitutions = []

        n_stored = 0
        n_all = 0

        for mother, daughter, mining_info in self.iter_substitutions():

            n_all += 1
            s = Substitution(self.ma, mother, daughter, mining_info)

            if not s.test_POS():
                continue
            if not s.test_real():
                continue

            self.substitutions.append(s)
            n_stored += 1

        print
        print 'Stored {} of {} mined substitutions.'.format(n_stored, n_all)

    def save_substitutions(self):
        """Save the mining results to pickle files.

        """

        print
        print 'Done. Saving substitutions...',
        ps.save(self.substitutions, self.savefile)
        print 'OK'

    def checkfile(self):
        try:
            di_fs.check_file(self.savefile)
        except Exception, msg:

            if self.ma.resume:
                warn(('*** A file for parameters {} already exists, not '
                      'overwriting it. Skipping this whole '
                      'argset. ***').format(di_fs.get_fileprefix(self.ma)))
                return False
            else:
                raise Exception(msg)

        return True

    def mine(self):
        """Load data, do the substitution mining, and save results."""

        self.ma.print_mining()
        self.savefile = di_fs.get_filename(self.ma)
        if not self.checkfile():
            return

        self.load_clusters()
        self.examine_substitutions()
        self.save_substitutions()
