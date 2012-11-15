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

import datastructure.memetracker_base as ds_mtb
from linguistics.memetracker import levenshtein
from linguistics.treetagger import tagger
from linguistics.lang_detection import langdetector
from linguistics.wordnettools import lemmatize
import datainterface.picklesaver as ps
import datainterface.redistools as rt
import settings as st


def frame_cluster_around_peak(cl, span_before=2 * 86400,
                                 span_after=2 * 86400):
    """Cut off quote occurrences in a Cluster around the 24h window with
    maximum activity.

    Arguments:
      * cl: the Cluster to work on

    Optional arguments:
      * span_before: time span (in seconds) to include before the beginning of
                     the max 24h window. Defaults to 2 days.
      * span_after: time span (in seconds) to include after the end of the max
                    24h window. Defaults to 2 days.

    Returns: a new framed Cluster.

    """

    cl.build_timeline()
    max_24h = find_max_24h_window(cl.timeline)

    start = max_24h - span_before
    end = max_24h + 86400 + span_after

    return frame_cluster(cl, start, end)


def frame_cluster(cl, start, end):
    """Cut off quote occurrences in a Cluster at the specified boundaries.

    Arguments:
      * cl: the Cluster to work on
      * start: time (in seconds from epoch) of the beginning of the target
               time window
      * end: time (in seconds from epoch) of the end of the target time window

    Returns: a new framed Cluster. If no quotes were kept after framing, None
             is returned.

    """

    import datastructure.memetracker as ds_mt

    framed_quotes = {}

    for qt in cl.quotes.itervalues():

        # Compute the starting time, ending time, time span, etc.

        qt.compute_attrs()

        # If the Quote intersects with the requested time window, include it.

        if (start <= qt.start <= end) or (qt.start <= start <= qt.end):

            framed_quote = frame_quote(qt, start, end)

            # If the Quote starts before 'start', ends after 'end', but has no
            # occurrences between 'start' and 'end' (in which case
            # 'framed_quote' is empty), exclude it.

            if framed_quote != None:
                framed_quotes[qt.id] = framed_quote

    # If no quotes were kept, return None.

    if len(framed_quotes) == 0:
        return None

    # Else, create the new framed Cluster.

    n_quotes = len(framed_quotes)
    tot_freq = sum([qt.tot_freq for qt in framed_quotes.values()])
    framed_cluster = ds_mt.Cluster(n_quotes=n_quotes, tot_freq=tot_freq,
                                   root=cl.root, cl_id=cl.id)
    framed_cluster.quotes = framed_quotes

    return framed_cluster


def frame_quote(qt, start, end):
    """Cut off quote occurrences in a Quote at the specified boundaries.

    Arguments:
      * qt: the Quote to work on
      * start: time (in seconds from epoch) of the beginning of the target
               time window
      * end: time (in seconds from epoch) of the end of the target time window

    Returns: a new framed Quote.

    """

    import datastructure.memetracker as ds_mt

    # Frame the Timeline of the Quote.

    framed_times = frame_timeline(qt, start, end)

    # Check its not empty.

    if len(framed_times) == 0:
        return None

    # Then create the new framed Quote.

    n_urls = len(set(framed_times))
    tot_freq = len(framed_times)
    framed_qt = ds_mt.Quote(n_urls=n_urls, tot_freq=tot_freq,
                            string=qt.string, qt_id=qt.id)
    framed_qt.url_times = framed_times
    framed_qt.current_idx = tot_freq

    # And compute its attributes.

    framed_qt.compute_attrs()

    return framed_qt


def frame_timeline(tm, start, end):
    """Cut off quote occurrences in a Timeline at the specified boundaries.

    Arguments:
      * tm: the Timeline to work on
      * start: time (in seconds from epoch) of the beginning of the target
               time window
      * end: time (in seconds from epoch) of the end of the target time window

    Returns: a new framed Timeline.

    """

    # Careful to return a copy, otherwise we just get a particular view of
    # the same memory space, which is bad for further modifications.

    return tm.url_times[np.where((start <= tm.url_times) *
                                 (tm.url_times <= end))].copy()


def find_max_24h_window(timeline, prec=30 * 60):
    """Find the 24h window of maximum activity in a Timeline.

    Arguments:
      * timeline: the Timeline to scan

    Optional arguments:
      * prec: the precision (in seconds) of the position of the returned time
              window. Defaults to half an hour.

    Returns: the time (in seconds from epoch) of the beginning of the maximum
             activity window.

    """

    # How many windows are we testing.

    n_windows = int(np.ceil(2 * 86400 / prec))

    # Compute the Timeline attributes.

    timeline.compute_attrs()

    # First estimation of where the maximum is; it has a precision of 1 day
    # (see details of Timeline.compute_attrs()).

    base_time = timeline.max_ipd_x_secs - 86400

    # Starting times of the time windows we're testing.

    start_times = np.arange(n_windows) * prec + base_time

    # Compute activity for each time window.

    ipd_all = np.zeros(n_windows)

    for i, stt in enumerate(start_times):
        ipd_all[i] = np.histogram(timeline.url_times, 1,
                                  (stt, stt + 86400))[0][0]

    # And get the max.

    return start_times[np.argmax(ipd_all)]


def filter_cluster(cl, min_tokens):
    """Filter a cluster to keep only English quotes longer than 'min_tokens'.

    Arguments:
      * cl: the cluster to filter
      * min_tokens: the minimum required number of words

    Returns: a new cluster (referencing the old quotes, not newly created
             ones) with only the quotes that have more than 'min_tokens'
             tokens, and that were detected to be in English. If the root of
             the cluster had less than 'min_tokens' or if was not detected as
             being English, or if no quotes inside the cluster were kept,
             None is returned.

    """

    import datastructure.memetracker as ds_mt

    # If the root has less than wanted, filter the whole cluster.

    if (len(tagger.Tokenize(cl.root)) < min_tokens or
        langdetector.detect(cl.root) != 'en'):
        return None

    # Else, examine each quote.

    filtered_quotes = {}

    for qt in cl.quotes.itervalues():

        if (len(tagger.Tokenize(qt.string)) >= min_tokens and
            langdetector.detect(qt.string) == 'en'):
            filtered_quotes[qt.id] = qt

    # If no quotes where kept, filter the whole cluster.

    if len(filtered_quotes) == 0:
        return None

    # Else, create the new filtered Cluster.

    n_quotes = len(filtered_quotes)
    tot_freq = sum([qt.tot_freq for qt in filtered_quotes.values()])
    filtered_cluster = ds_mt.Cluster(n_quotes=n_quotes, tot_freq=tot_freq,
                                     root=cl.root, cl_id=cl.id)
    filtered_cluster.quotes = filtered_quotes

    return filtered_cluster


class ClusterAnalyze(ds_mtb.ClusterBase):

    """Mixin class to use in the full Cluster class. Includes analysis methods.

    Methods:
    * build_timebags: build a number of TimeBags from a Cluster
    * built_timebag: build a TimeBag from a Cluster

    """

    def build_timebags(self, n_bags, cumulative=False):
        """Build a number of TimeBags from a Cluster.

        Arguments:
        * n_bags: the number of TimeBags to chop the Cluster into

        Keyword arguments:
        * cumulative: boolean specifying if the timebags built should be
                        time-cumulative or not. Defaults to False.

        Returns: a list of TimeBags.

        """

        import datastructure.memetracker as ds_mt

        # Build the Timeline for the Cluster, set the parameters for the TimeBags.

        self.build_timeline()

        step = int(round(self.timeline.span.total_seconds() / n_bags))
        cl_start = self.timeline.start

        # Create the sequence of TimeBags.

        timebags = []
        dontcum = not cumulative

        for i in xrange(n_bags):
            timebags.append(ds_mt.TimeBag(self, cl_start + i * step * dontcum,
                                        cl_start + (i + 1) * step))

        return timebags

    def build_timebag(self, n_bags, end, cumulative=False):
        """Build a TimeBag from a Cluster.

        Arguments:
        * n_bags: the number of TimeBags we're slicing the cluster into
        * end: the timestamp at which the timebag should end

        Keyword arguments:
        * cumulative: boolean specifying if the timebag built should be
                        time-cumulative or not. If True, the timebag built
                        starts at the beginning of the cluster, else it starts
                        at `end - cluster_span / n_bags`. Defaults to False.

        """

        import datastructure.memetracker as ds_mt

        # Build the timeline for the Cluster, set the parameters for the
        # TimeBag

        self.build_timeline()
        cl_start = self.timeline.start

        if not cumulative:

            span = int(round(self.timeline.span.total_seconds() / n_bags))
            start = max(cl_start, end - span)

        else:
            start = cl_start

        return ds_mt.TimeBag(self, start, end)


def build_n_quotes_to_clusterids(clusters):
    """Build a dictionary associating number of Quotes to Cluster ids having
    that number of quotes.

    Arguments:
      * The RedisDataAccess Clusters connection or dict of Clusters to work on

    Returns: the dict of 'number of Quotes' -> 'sequence of Cluster ids'.

    """

    inv_cl_lengths = {}

    for cl_id, cl in clusters.iteritems():

        if inv_cl_lengths.has_key(cl.n_quotes):
            inv_cl_lengths[cl.n_quotes].append(cl_id)
        else:
            inv_cl_lengths[cl.n_quotes] = [cl_id]

    return inv_cl_lengths


def build_quotelengths_to_n_quote(clusters):
    """Build a dict associating Quote string lengths to the number of Quotes
    having that string length.

    Arguments:
      * The RedisDataAccess Clusters connection or dict of Clusters to work on

    Returns: the dict of 'Quote string lengths' -> 'number of Quotes having
             that string length'.

    """

    inv_qt_lengths = {}

    for cl in clusters.itervalues():

        for qt in cl.quotes.itervalues():

            n_words = len(tagger.Tokenize(qt.string.lower()))

            if inv_qt_lengths.has_key(n_words):
                inv_qt_lengths[n_words] += 1
            else:
                inv_qt_lengths[n_words] = 1

    return inv_qt_lengths


def dict_plusone(d, key):
    """Add one to d[key] or set it to one if non-existent."""
    if d.has_key(key):
        d[key] += 1
    else:
        d[key] = 1


def gen_results_dict(gen=list):
    return dict((fdata, dict((fname, gen()) for fname in ffiles.iterkeys()))
                for fdata, ffiles
                in st.memetracker_subst_features.iteritems())


class ProgressInfo(object):

    """Print progress information.

    Methods:
      * __init__: initialize the instance
      * next_step: increase progress counter and print info if needed

    """

    def __init__(self, n_tot, n_info, label='objects'):
        """Initialize the instance.

        Arguments:
          * n_tot: the total number of items through which we are making
                   progress
          * n_info: the number of informations messages to be displayed

        Keyword arguments:
          * label: a label for printing information (i.e. what kind of objects
                   are we making progress through?). Defaults to 'objects'.

        """

        self.progress = 0
        self.n_tot = n_tot
        self.info_step = max(int(round(n_tot / n_info)), 1)
        self.label = label

    def next_step(self):
        """Increase progress counter and print info if needed."""
        self.progress += 1
        if self.progress % self.info_step == 0:
            print '  {} % ({} / {} {})'.format(
                int(round(100 * self.progress / self.n_tot)), self.progress,
                self.n_tot, self.label)


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
      * subst_lemmatize: lemmatize a substitution if argset asks for it
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

        if not argset['lemmatizing']:
            file_prefix += 'N'

        file_prefix += 'L_'

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
        print '  lemmatizing = {}'.format(argset['lemmatizing'])
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
        """Lemmatize a substitution using TreeTagger and Wordnet, if argset
        asks for it."""
        if argset['lemmatizing']:

            t1 = tagger.Lemmatize(mother)[idx]
            t2 = tagger.Lemmatize(daughter)[idx]

            lem1 = lemmatize(t1)
            lem2 = lemmatize(t2)

            if argset['verbose']:
                print ("Lemmatized: '" + lem1 + "' -> '" +
                       lem2 + "'")

        else:

            lem1 = mother.tokens[idx]
            lem2 = daughter.tokens[idx]

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

    def subst_try_save(self, argset, features, lem1, lem2, details,
                       tdata, tdata_d, n_stored, suscept_data):
        """Save a substitution if it is referenced in the feature list."""

        for fdata in features.iterkeys():

            for fname in features[fdata].iterkeys():

                try:
                    tdata[fdata][fname].append([features[fdata][fname][lem1],
                                                features[fdata][fname][lem2]])
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

        if argset['lemmatizing']:
            lem_mother = tagger.Lemmatize(mother)
        else:
            lem_mother = mother

        for tlem in lem_mother:

            if argset['lemmatizing']:
                lem = lemmatize(tlem)
            else:
                lem = tlem

            for fdata in suscept_data.iterkeys():

                for fname, fsuscept in suscept_data[fdata].iteritems():

                    if data['features'][fdata][fname].has_key(lem):
                        dict_plusone(fsuscept['possibilities'], lem)

    def examine_substitutions(self, argset, data):
        """Examine substitutions and retain only those we want.

        Arguments:
          * argset: the argset for the analysis
          * data: the dict containing the data to be examined

        Returns: a dict containing six items: three Nx2 numpy arrays, each one
                 containing the features (WN PR scores, WN degrees, FA PR
                 scores) of the substituted and substitutant words from the
                 substitutions that were kept after filtering; three lists of
                 dicts containing the details of each substitution stored, for
                 each feature.

        Details: ***

        """

        print
        print 'Doing substitution analysis:'

        # Results of the analysis

        transitions = gen_results_dict()
        transitions_d = gen_results_dict()
        suscept_data = gen_results_dict(lambda: {'possibilities': {},
                                                 'realised': {}})
        n_stored = gen_results_dict(int)
#        suscept_data = dict((fdata, {'possibilities': {}, 'realised': {}})
#                             for fdata
#                             in st.memetracker_subst_features.iterkeys())
#        n_stored = dict((fdata, 0)
#                        for fdata
#                        in st.memetracker_subst_features.iterkeys())
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
            lem1, lem2 = self.subst_lemmatize(argset, mother, daughter, idx)
            if not self.subst_test_real(argset, lem1, lem2):
                continue

            details = {'mother': mother,
                       'daughter': daughter,
                       'idx': idx,
                       'lem1': lem1,
                       'lem2': lem2,
                       'subst_info': subst_info}

            self.subst_try_save(argset, data['features'], lem1, lem2, details,
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
                                            'lemmatizing': True,
                                            'substitutions': substitutions,
                                            'substrings': bool(int(subsgs)),
                                            'POS': pos,
                                            'verbose': False,
                                            'n_timebags': 0,
                                            'resume': args.resume})

                        else:

                            for n_timebags in args.n_timebagss:

                                argsets.append({'ff': ff,
                                            'lemmatizing': True,
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

        The analysis is always done with framing-filtering and lemmatizing
        activated.

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
