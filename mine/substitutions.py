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

from multiprocessing import cpu_count, Pool
from warnings import warn

import numpy as np

from linguistics.distance import levenshtein
from linguistics.treetagger import tagger
from linguistics.wn import lemmatize
import datainterface.picklesaver as ps
import datainterface.redistools as rt
from util import dict_plusone, ProgressInfo
import settings as st


def gen_results_dict(gen=list):
    return dict((fdata, dict((fname, gen()) for fname in ffiles.iterkeys()))
                for fdata, ffiles
                in st.memetracker_subst_features.iteritems())



class SubstitutionAnalysis(object):

    """Analyze the 1-word changes in the MemeTracker dataset.

    This class looks at features of words that are substituted through time in
    the MemeTracker Clusters. The features are the Wordnet PageRank scores of
    the words, their degree in the Wordnet graph, and the Free Association
    PageRank scores.

    Methods:
      * __init__: set the number of processes for multi-threading
      * get_save_files: get the filenames where data is to be saved; check
                        they don't already exist
      * print_argset: print an argset to stdout
      * load_data: load the data from pickle files
      * itersubstitutions_all: iterate through all substitutions according to the
                               given argset
      * subst_print_info: print information about the substitution if argset
                          asks for it
      * subst_test_POS: test for correspondence of POS tags in a substitution
      * subst_lemmatize: lemmatize a substitution
      * subst_test_real: test if two words really form a substitution, or are
                         in fact only variations of the same root
      * subst_try_save_wn: save a substitution if it is referenced in the WN
                           feature list
      * subst_try_save_fa: save a substitution if it is referenced in the FA
                           feature list
      * subst_update_possibilities: update the counts of what words can be
                                    substituted
      * examine_substitutions: examine substitutions and retain only those we
                               want
      * save_results: save the analysis results to pickle files
      * create_argsets: create a list of possible argset dicts, according to
                        args from the command line
      * analyze: load data, do the substitution analysis, and save results
      * analyze_all: run 'analyze' with various argsets
      * put_analyze: put an analysis job in the queue
      * analyze_all_mt: run 'analyze' with various argsets, multi-threaded

    """

    def __init__(self):
        """Set the number of processes for multi-threading."""
        self.n_cpu = cpu_count()
        self.n_proc = self.n_cpu - 1
        self.pos_wn_to_tt = {'a': 'J', 'n': 'N', 'v': 'V', 'r': 'R'}

    @classmethod
    def get_save_files(cls, argset, readonly=False):
        """Get the filenames where data is to be saved to or read from; check
        either that they don't already exist, or that they do exist.

        Arguments:
          * argset: an argset of arguments (= processed arguments from
                    command line)

        Keyword arguments:
          * readonly: boolean specifying the behaviour of checking of files.
                      False means we want to be warned if the files already
                      exist, True means we want to be warned if the files
                      don't exist. Defaults to False.

        Returns: a dict of filenames corresponding to the data to save, or
                 None if a check failed.

        """

        # Create the file prefix according to 'argset'.

        file_prefix = ''

        file_prefix += 'F{}_'.format(argset['ff'])

        file_prefix += 'S{}_'.format(argset['substitutions'])

        if not argset['substrings']:
            file_prefix += 'N'

        file_prefix += 'sub_'

        file_prefix += 'P{}_'.format(argset['POS'])

        if argset['substitutions'] != 'time':
            file_prefix += str(argset['n_timebags']) + '_'

        filename = st.memetracker_subst_results_pickle.format(file_prefix)

        # Check that the destination doesn't already exist.

        try:
            st.check_file(filename, look_for_absent=readonly)

        except Exception, msg:

            if readonly:

                warn('{}: not found'.format(argset))
                return None

            else:

                if argset['resume']:

                    warn(('*** A file for parameters {} already exists, not '
                          'overwriting it. Skipping the whole '
                          'argset. ***').format(file_prefix))
                    return None

                else:

                    raise Exception(msg)

        return filename

    def print_argset(self, argset):
        """Print an argset to stdout."""
        print
        print 'Doing analysis with the following argset:'
        print '  ff = {}'.format(argset['ff'])
        print '  substitutions = {}'.format(argset['substitutions'])
        print '  substrings = {}'.format(argset['substrings'])
        print '  POS = {}'.format(argset['POS'])
        print '  verbose = {}'.format(argset['verbose'])
        print '  n_timebags = {}'.format(argset['n_timebags'])

    def load_data(self, argset):
        """Load the data from pickle files.

        Arguments:
          * argset: an argset of arguments for the analysis

        Returns: a dict containing the various data structures loaded.

        """

        print
        print ('Connecting to redis server for cluster data, '
               'loading PageRank and degree data from pickle...'),

        ff_dict = {'full': st.redis_mt_clusters_pref,
                   'framed': st.redis_mt_clusters_framed_pref,
                   'filtered': st.redis_mt_clusters_filtered_pref,
                   'ff': st.redis_mt_clusters_ff_pref}

        clusters = rt.RedisReader(ff_dict[argset['ff']])
        features = {}

        for fdata, ffiles in st.memetracker_subst_features.iteritems():

            features[fdata] = {}

            for fname, filename in ffiles.iteritems():
                features[fdata][fname] = \
                        ps.load(filename.format(argset['POS']))

        print 'OK'

        return {'clusters': clusters, 'features': features }

    def itersubstitutions_all(self, argset, data):
        """Iterate through all substitutions according to the given argset."""
        progress = ProgressInfo(len(data['clusters']), 100, 'clusters')

        for cl in data['clusters'].itervalues():

            progress.next_step()
            for mother, daughter, subst_info in cl.iter_substitutions[
                                            argset['substitutions']](argset):
                yield (mother, daughter, subst_info)

    def subst_print_info(self, argset, mother, daughter, idx, subst_info):
        """Print information about the substitution if argset asks for it."""
        if argset['verbose']:

            raw_input()
            print
            print ("***** SUBST (cl #{} / {}) ***** '".format(mother.cl_id,
                                                              subst_info) +
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

    def subst_test_POS(self, argset, mother, daughter, idx):
        """Test for correspondence of POS tags in a substitution."""
        ret = True

        if argset['POS'] == 'all':

            if daughter.POS_tags[idx][0] != mother.POS_tags[idx][0]:
                if argset['verbose']:
                    print 'Stored: NONE (different POS)'
                ret = False

        else:

            if (daughter.POS_tags[idx][0] !=
                self.pos_wn_to_tt[argset['POS']] or
                mother.POS_tags[idx][0] != self.pos_wn_to_tt[argset['POS']]):
                if argset['verbose']:
                    print 'Stored: NONE (wrong POS)'
                ret = False

        return ret

    def subst_lemmatize(self, argset, mother, daughter, idx):
        """Lemmatize a substitution using TreeTagger and Wordnet."""
        t1 = tagger.Lemmatize(mother)[idx]
        t2 = tagger.Lemmatize(daughter)[idx]

        lem1 = lemmatize(t1)
        lem2 = lemmatize(t2)

        if argset['verbose']:
            print ("Lemmatized: '" + lem1 + "' -> '" +
                    lem2 + "'")
        return (lem1, lem2)

    def subst_test_real(self, argset, lem1, lem2):
        """Test if two words really form a substitution, or are in fact only
        variations of the same root."""
        ret = True

        if levenshtein(lem1, lem2) <= 1:
            if argset['verbose']:
                print 'Stored: NONE (not substitution)'
            ret = False

        return ret

    def subst_try_save(self, argset, features, word1, word2, lem1, lem2,
                       details, tdata, tdata_d, n_stored, suscept_data):
        """Save a substitution if it is referenced in the feature list."""

        for fdata in features.iterkeys():

            for fname in features[fdata].iterkeys():

                # If the feature uses lemmatizing, then do it.
                if st.memetracker_subst_features_lem[fdata][fname]:
                    save1, save2 = lem1, lem2
                else:
                    save1, save2 = word1, word2

                try:
                    tdata[fdata][fname].append([features[fdata][fname][save1],
                                                features[fdata][fname][save2]])
                    tdata_d[fdata][fname].append(details)

                    n_stored[fdata][fname] += 1
                    dict_plusone(suscept_data[fdata][fname]['realised'], lem1)

                    if argset['verbose']:
                        print 'Stored: %s %s YES' % (fdata, fname)

                except KeyError:

                    if argset['verbose']:
                        print 'Stored: %s %s NO (not referenced)' % (fdata,
                                                                     fname)

    def subst_update_possibilities(self, argset, data, mother, suscept_data):
        """Update the counts of what words can be substituted."""

        lem_mother = tagger.Lemmatize(mother)

        for tlem in lem_mother:

            lem = lemmatize(tlem)

            for fdata in suscept_data.iterkeys():

                for fname, fsuscept in suscept_data[fdata].iteritems():

                    if data['features'][fdata][fname].has_key(lem):
                        dict_plusone(fsuscept['possibilities'], lem)

    def examine_substitutions(self, argset, data):
        """Examine substitutions and retain only those we want.

        Arguments:
          * argset: the argset for the analysis
          * data: the dict containing the data to be examined

        Returns: TODO

        Details: TODO

        """

        print
        print 'Doing substitution analysis:'

        # Results of the analysis

        transitions = gen_results_dict()
        transitions_d = gen_results_dict()
        suscept_data = gen_results_dict(lambda: {'possibilities': {},
                                                 'realised': {}})
        n_stored = gen_results_dict(int)
        n_all = 0

        for mother, daughter, subst_info in self.itersubstitutions_all(argset,
                                                                       data):

            self.subst_update_possibilities(argset, data, mother,
                                            suscept_data)

            n_all += 1
            idx = np.where([w1 != w2 for (w1, w2) in
                            zip(daughter.tokens, mother.tokens)])[0]

            self.subst_print_info(argset, mother, daughter, idx, subst_info)
            if not self.subst_test_POS(argset, mother, daughter, idx):
                continue
            word1, word2 = mother.tokens[idx], daughter.tokens[idx]
            lem1, lem2 = self.subst_lemmatize(argset, mother, daughter, idx)
            if not self.subst_test_real(argset, lem1, lem2):
                continue

            details = {'mother': mother,
                       'daughter': daughter,
                       'idx': idx,
                       'norm_idx': idx / (len(daughter.tokens) - 1),
                       'word1': word1,
                       'word2': word2,
                       'lem1': lem1,
                       'lem2': lem2,
                       'subst_info': subst_info}

            self.subst_try_save(argset, data['features'], word1, word2,
                                lem1, lem2, details,
                                transitions, transitions_d, n_stored,
                                suscept_data)

        print
        print 'Examined {} substitutions.'.format(n_all)

        for fdata, ns in n_stored.iteritems():
            print 'Stored {} substitutions with {}'.format(n_stored[fdata], fdata)

        return {'transitions': transitions, 'transitions_d': transitions_d,
                'suscept_data': suscept_data}

    def save_results(self, files, results):
        """Save the analysis results to pickle files.

        Arguments:
          * files: the dict of filenames as given by 'get_save_files'
          * results: the dict of results as given by 'examine_substitutions'

        """

        print
        print 'Done. Saving data...',

        for fdata, trdict in results['transitions'].iteritems():

            for fname, trs in trdict.iteritems():
                results['transitions'][fdata][fname] = np.array(trs)

        ps.save(results, files)
        print 'OK'

    @classmethod
    def create_argsets(self, args):
        """Create a list of possible argset dicts, according to args from the
        command line.

        Arguments:
          * args: the dict of args passed in from the command line

        Returns:
          * argsets: a list of dicts, each one being an acceptable dict for
                     self.analyze.

        """

        argsets = []

        for ff in args.ffs:

            for pos in args.POSs:

                for substitutions in args.substitutionss:

                    for subsgs in args.substringss:

                        if substitutions in ['time', 'growtbgs']:

                            argsets.append({'ff': ff,
                                            'substitutions': substitutions,
                                            'substrings': bool(int(subsgs)),
                                            'POS': pos,
                                            'verbose': False,
                                            'n_timebags': 0,
                                            'resume': args.resume})

                        else:

                            for n_timebags in args.n_timebagss:

                                argsets.append({'ff': ff,
                                            'substitutions': substitutions,
                                            'substrings': bool(int(subsgs)),
                                            'POS': pos,
                                            'verbose': False,
                                            'n_timebags': int(n_timebags),
                                            'resume': args.resume})

        return argsets

    def analyze(self, argset):
        """Load data, do the substitution analysis, and save results.

        Arguments:
          * argset: the argset for the analysis (= transformed args from
                    command line)

        """

        self.print_argset(argset)
        files = self.get_save_files(argset)

        if files == None:
            return

        data = self.load_data(argset)
        results = self.examine_substitutions(argset, data)
        self.save_results(files, results)

    def analyze_all(self, args):
        """Run 'analyze' with various argsets.

        Arguments:
          * args: the dict of args passed in from the command line

        """

        print
        print ('Starting substitution analysis, for timebag '
               'slicings {}, POSs {}, datasets {}, substitutionss {}, and '
               'substringss {} ...').format(args.n_timebagss, args.POSs,
                                            args.ffs, args.substitutionss,
                                            args.substringss)

        argsets = self.create_argsets(args)

        for argset in argsets:
            self.analyze(argset)

    def analyze_all_mt(self, args):
        """Run 'analyze' with various argsets, multi-threaded."""

        print
        print ('Starting multi-threaded substitution analysis, for timebag '
               'slicings {}, POSs {}, datasets {}, substitutionss {}, and '
               'substringss {} ...').format(args.n_timebagss, args.POSs,
                                            args.ffs, args.substitutionss,
                                            args.substringss)

        argsets = self.create_argsets(args)
        n_jobs = len(argsets)

        print
        print 'Using {} workers to do {} jobs.'.format(self.n_proc, n_jobs)

        pool = Pool(processes=self.n_proc, maxtasksperchild=1)
        res = pool.map_async(self.analyze, argsets)

        # The timeout here is to be able to keyboard-interrupt.
        # See http://bugs.python.org/issue8296 for details.

        res.wait(1e12)
