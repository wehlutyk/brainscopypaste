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


def gen_results_dict(gen=list):
    return dict((fdata, dict((fname, gen()) for fname in ffiles.iterkeys()))
                for fdata, ffiles
                in st.memetracker_subst_features.iteritems())


class SubstitutionsMiner(object):

    pos_wn_to_tt = {'a': 'J', 'n': 'N', 'v': 'V', 'r': 'R'}

    def __init__(self):
        """Set the number of processes for multi-threading."""
        self.n_cpu = cpu_count()
        self.n_proc = self.n_cpu - 1

    def load_clusters(self, ma):
        """Load the data from pickle files.

        Arguments:
          * argset: an argset of arguments for the analysis

        Returns: a dict containing the various data structures loaded.

        """

        print
        print 'Connecting to redis server for cluster data...',

        ff_dict = {'full': st.redis_mt_clusters_pref,
                   'framed': st.redis_mt_clusters_framed_pref,
                   'filtered': st.redis_mt_clusters_filtered_pref,
                   'ff': st.redis_mt_clusters_ff_pref}
        clusters = rt.RedisReader(ff_dict[ma.ff])

        print 'OK'

        return clusters

    def iter_substitutions(self, ma, clusters):
        """Iterate through all substitutions according to the given MiningArgs."""
        progress = ProgressInfo(len(clusters), 100, 'clusters')

        for cl in clusters.itervalues():

            progress.next_step()
            for mother, daughter, mining_info in cl.iter_substitutions[ma.model](ma):
                yield (mother, daughter, mining_info)

    def subst_print_info(self, ma, mother, daughter, idx, mining_info):
        """Print information about the substitution if ma asks for it."""
        if ma.verbose:

            raw_input()
            print
            print ("***** SUBST (cl #{} / {}) ***** '".format(mother.cl_id,
                                                              mining_info) +
                   '{}/{}'.format(mother.tokens[idx],
                                  mother.POS_tags[idx]) +
                   "' -> '" +
                   '{}/{}'.format(daughter.tokens[idx],
                                  daughter.POS_tags[idx]) +
                   "'")
            print mother
            print '=>'
            print daughter
            print

    def subst_test_POS(self, ma, mother, daughter, idx):
        """Test for correspondence of POS tags in a substitution."""
        ret = True

        if ma.POS == 'all':

            if daughter.POS_tags[idx][0] != mother.POS_tags[idx][0]:
                if ma.verbose:
                    print 'Not kept (different POS)'
                ret = False

        else:

            if (daughter.POS_tags[idx][0] !=
                self.pos_wn_to_tt[ma.POS] or
                mother.POS_tags[idx][0] != self.pos_wn_to_tt[ma.POS]):
                if ma.verbose:
                    print 'Not kept (wrong POS)'
                ret = False

        return ret

    def subst_lemmatize(self, ma, mother, daughter, idx):
        """Lemmatize a substitution using TreeTagger and Wordnet."""
        t1 = tagger.Lemmatize(mother)[idx]
        t2 = tagger.Lemmatize(daughter)[idx]

        lem1 = lemmatize(t1)
        lem2 = lemmatize(t2)

        if ma.verbose:
            print ("Lemmatized: '" + lem1 + "' -> '" +
                    lem2 + "'")
        return (lem1, lem2)

    def subst_test_real(self, ma, lem1, lem2):
        """Test if two words really form a substitution, or are in fact only
        variations of the same root."""
        ret = True

        if levenshtein(lem1, lem2) <= 1:
            if ma.verbose:
                print 'Not kept (not substitution)'
            ret = False

        return ret

    def examine_substitutions(self, ma, clusters):
        """Examine substitutions and retain only those we want.

        Arguments:
          * argset: the argset for the analysis
          * data: the dict containing the data to be examined

        Returns: TODO

        Details: TODO

        """

        print
        print 'Mining substitutions:'

        # Results of the mining
        substitutions = []

        n_stored = 0
        n_all = 0

        for mother, daughter, mining_info in self.iter_substitutions(ma, clusters):

            n_all += 1
            idx = np.where([w1 != w2 for (w1, w2) in
                            zip(daughter.tokens, mother.tokens)])[0]

            self.subst_print_info(ma, mother, daughter, idx, mining_info)
            if not self.subst_test_POS(ma, mother, daughter, idx):
                continue
            word1, word2 = mother.tokens[idx], daughter.tokens[idx]
            lem1, lem2 = self.subst_lemmatize(ma, mother, daughter, idx)
            if not self.subst_test_real(ma, lem1, lem2):
                continue

            subst = {'mother': mother,
                     'daughter': daughter,
                     'idx': idx,
                     'word1': word1,
                     'word2': word2,
                     'lem1': lem1,
                     'lem2': lem2,
                     'mining_info': mining_info}
            substitutions.append(subst)
            n_stored += 1

        print
        print 'Stored {} of {} mined substitutions.'.format(n_stored, n_all)

        return substitutions

    def save_substitutions(self, savefile, substitutions):
        """Save the analysis results to pickle files.

        Arguments:
          * files: the dict of filenames as given by 'get_save_files'
          * results: the dict of results as given by 'examine_substitutions'

        """

        print
        print 'Done. Saving substitutions...',
        ps.save(substitutions, savefile)
        print 'OK'

    def mine(self, ma):
        """Load data, do the substitution mining, and save results."""

        ma.print_mining()
        savefile = di_fs.get_save_file(ma)

        if savefile == None:
            return

        clusters = self.load_clusters(ma)
        substitutions = self.examine_substitutions(ma, clusters)
        self.save_substitutions(savefile, substitutions)

    def mine_multiple(self, mma):
        """Run 'mine' with various argsets.

        """

        mma.print_mining()

        for ma in mma:
            self.mine(ma)

    def mine_multiple_mt(self, mma):
        """Run 'minee' with various argsets, multi-threaded."""

        mma.print_mining()
        n_jobs = len(mma)

        print
        print 'Using {} workers to do {} jobs.'.format(self.n_proc, n_jobs)

        pool = LoggingPool(processes=self.n_proc, maxtasksperchild=1)
        res = pool.map_async(self.mine, mma.mas)

        # The timeout here is to be able to keyboard-interrupt.
        # See http://bugs.python.org/issue8296 for details.

        res.wait(1e12)
