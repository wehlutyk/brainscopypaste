#!/usr/bin/env python # -*- coding: utf-8 -*-

"""Analyze data from the MemeTracker dataset.

Methods:
  * frame_cluster_around_peak: cut off quote occurrences in a Cluster around
                               the 24h window with maximum activity
  * frame_cluster: cut off quote occurrences in a Cluster at the specified
                   boundaries
  * frame_quote: cut off quote occurrences in a Quote at the specified
                 boundaries
  * frame_timeline: cut off quote occurrences in a Timeline at the specified
                    boundaries
  * find_max_24h_window: find the 24h window of maximum activity in a Timeline
  * build_n_quotes_to_clusterids: build a dict associating number of Quotes to
                                  Cluster ids having that number of quotes
  * build_quoteslengths_to_quoteids: build a dict associating Quote string
                                     lengths to the number of Quotes having
                                     that string length
  * dict_plusone: add one to d[key] or set it to one if non-existent

Classes:
  * ProgressInfo: print progress information
  * SubstitutionAnalysis: analyze the 1-word changes in the MemeTracker
                          dataset
  * ClusterAnalyze: mixin class to use in the full Cluster class. Includes
                    analysis methods.

"""


from __future__ import division

from multiprocessing import cpu_count
from functools import partial

import numpy as np

from linguistics.distance import levenshtein
from linguistics.treetagger import tagger
from linguistics.wn import lemmatize
import datainterface.picklesaver as ps
import datainterface.redistools as rt
import datainterface.fs as di_fs
from util import ProgressInfo
from util.mp import LoggingPool
import settings as st


class Substitution(object):

    pos_wn_to_tt = {'a': 'J', 'n': 'N', 'v': 'V', 'r': 'R'}

    def __init__(self, ma, mother, daughter, mining_info):
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
        """Lemmatize the substitution using TreeTagger and Wordnet."""
        t1 = tagger.Lemmatize(self.mother)[self.idx]
        t2 = tagger.Lemmatize(self.daughter)[self.idx]

        self.lem1 = lemmatize(t1)
        self.lem2 = lemmatize(t2)

        if self.ma.verbose:
            print ("Lemmatized: '" + self.lem1 + "' -> '" +
                    self.lem2 + "'")

    def print_info(self):
        """Print information about the substitution if ma asks for it."""
        if self.ma.verbose:

            raw_input()
            print
            print ("***** SUBST (cl #{} / {}) ***** '".format(self.mother.cl_id,
                                                              self.mining_info) +
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
        """Test for correspondence of POS tags in a substitution."""
        ret = True

        if self.ma.POS == 'all':

            if self.daughter.POS_tags[self.idx][0] != self.mother.POS_tags[self.idx][0]:
                if self.ma.verbose:
                    print 'Not kept (different POS)'
                ret = False

        else:

            if (self.daughter.POS_tags[self.idx][0] !=
                self.pos_wn_to_tt[self.ma.POS] or
                self.mother.POS_tags[self.idx][0] != self.pos_wn_to_tt[self.ma.POS]):
                if self.ma.verbose:
                    print 'Not kept (wrong POS)'
                ret = False

        return ret

    def test_real(self):
        """Test if the two words really form a substitution, or are in fact only
        variations of the same root."""
        ret = True

        if levenshtein(self.lem1, self.lem2) <= 1:
            if self.ma.verbose:
                print 'Not kept (not substitution)'
            ret = False

        return ret


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
        """Iterate through all substitutions according to the given MiningArgs."""
        progress = ProgressInfo(len(self.clusters), 100, 'clusters')

        for cl in self.clusters.itervalues():

            progress.next_step()
            for mother, daughter, mining_info in cl.iter_substitutions[self.ma.model](self.ma):
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

    def mine(self):
        """Load data, do the substitution mining, and save results."""

        self.ma.print_mining()
        self.savefile = di_fs.get_filename(self.ma)

        if self.savefile == None:
            return

        self.load_clusters()
        self.examine_substitutions()
        self.save_substitutions()

    @classmethod
    def mine_multiple(cls, mma):
        """Run 'mine' with various argsets.

        """

        mma.print_mining()

        for ma in mma:
            sm = cls(ma)
            sm.mine()

    @classmethod
    def mine_multiple_mt(cls, mma):
        """Run 'minee' with various argsets, multi-threaded."""

        mma.print_mining()
        n_jobs = len(mma)

        n_cpu = cpu_count()
        n_proc = n_cpu - 1

        print
        print 'Using {} workers to do {} jobs.'.format(n_proc, n_jobs)

        pool = LoggingPool(processes=n_proc, maxtasksperchild=1)
        mine = partial(cls, start=True)
        res = pool.map_async(mine, mma)

        # The timeout here is to be able to keyboard-interrupt.
        # See http://bugs.python.org/issue8296 for details.

        res.wait(1e12)
