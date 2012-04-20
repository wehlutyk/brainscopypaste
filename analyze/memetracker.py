#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
  * build_timebags: build a number of TimeBags from a Cluster
  * build_n_quotes_to_clusterids: build a dict associating number of Quotes to
                                  Cluster ids having that number of quotes
  * build_quoteslengths_to_quoteids: build a dict associating Quote string
                                     lengths to the number of Quotes having
                                     that string length
  * _build_timebag_transitions: recursively build the list of possible
                                transitions from a number of TimeBags (private
                                method, used by 'build_timebag_transitions')
  * build_timebag_transitions: build the list of possible transitions from a
                               number of TimeBags

Classes:
  * SubstitutionAnalysis: analyze the 1-word changes in the MemeTracker
                          dataset

"""


from __future__ import division

from multiprocessing import Process, Queue, cpu_count

from nltk.corpus import wordnet as wn
import numpy as np

import datastructure.memetracker as ds_mt
from linguistics.memetracker import levenshtein
from linguistics.treetagger import TreeTaggerTags
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
    
    Returns: a new framed Cluster.
    
    """
    
    framed_quotes = {}
    
    for qt in cl.quotes.values():
        
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
    
    # Create the new framed Cluster.
    
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
    
    for i, st in enumerate(start_times):
        ipd_all[i] = np.histogram(timeline.url_times, 1,
                                  (st, st + 86400))[0][0]
    
    # And get the max.
    
    return start_times[np.argmax(ipd_all)]


def build_timebags(cluster, n_bags):
    """Build a number of TimeBags from a Cluster.
    
    Arguments:
      * cluster: the Cluster to work on
      * n_bags: the number of TimeBags to chop the Cluster into
    
    Returns: a list of TimeBags.
    
    """
    
    # Build the Timeline for the Cluster, set the parameters for the TimeBags.
    
    cluster.build_timeline()
    
    step = int(round(cluster.timeline.span.total_seconds() / n_bags))
    cl_start = cluster.timeline.start
    
    # Create the sequence of TimeBags.
    
    timebags = []
    
    for i in xrange(n_bags):
        timebags.append(ds_mt.TimeBag(cluster, cl_start + i * step,
                                      cl_start + (i + 1) * step))
    
    return timebags


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
    tagger = TreeTaggerTags(TAGLANG='en', TAGDIR=st.treetagger_TAGDIR,
                            TAGINENC='utf-8', TAGOUTENC='utf-8')
    
    for cl in clusters.itervalues():
        
        for qt in cl.quotes.itervalues():
            
            n_words = len(tagger.Tokenize(qt.string.lower()))
            
            if inv_qt_lengths.has_key(n_words):
                inv_qt_lengths[n_words] += 1
            else:
                inv_qt_lengths[n_words] = 1
    
    return inv_qt_lengths


def _build_timebag_transitions(bag_indices, transitions):
    """Recursively build the list of possible transitions from a number of
    TimeBags.
    
    Arguments:
      * bag_indices: the indices of the TimeBags between which to build
                     transitions
      * transitions: the list passed on to the recursive instances of the
                     method, containing what transitions have already been
                     generated
    
    Returns: a list of tuples, each tuple representing a transition from one
             TimeBag to a later one.
    
    """
    
    if len(bag_indices) > 1:
        
        transitions.extend([(bag_indices[0], idx) for idx in bag_indices[1:]])
        _build_timebag_transitions(bag_indices[1:], transitions)
        
    else:
        return []


def build_timebag_transitions(n_timebags):
    """Build the list of possible transitions from a number of TimeBags.
    
    The real work is done by the '_build_timebag_transitions' method.
    
    Arguments:
      * the number of TimeBags
    
    Returns: a list of tuples, each tuple representing a transition from one
             TimeBag to a later one.
    
    """
    
    transitions = []
    _build_timebag_transitions(range(n_timebags), transitions)
    
    return transitions


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
      * print_args: print the arguments to stdout
      * load_data: load the data from pickle files
      * examine_substitutions: examine substitutions and retain only those we
                               want
      * save_results: save the analysis results to pickle files
      * create_args_list: create a list of possible args dicts, according to
                          requested timebag slicings
      * analyze: load data, do the substitution analysis, and save results
      * analyze_all: run 'analyze' with various timebag slicings
      * put_analyze: put an analysis job in the queue
      * analyze_all_mt: run 'analyze' with various timebag slicings,
                        multi-threaded
    
    """
    
    def __init__(self):
        """Set the number of processes for multi-threading."""
        self.n_cpu = cpu_count()
        self.n_proc = self.n_cpu - 1
    
    def get_save_files(self, args):
        """Get the filenames where data is to be saved; check they don't
        already exist.
        
        Arguments:
          * args: the dict of arguments, gotten from the command line or
                  manually set
        
        Returns: a dict of filenames corresponding to the data to save.
        
        """
        
        # Create the file prefix according to 'args'.
        
        file_prefix = ''
        
        if not args['framing']:
            file_prefix += 'N'
        
        file_prefix += 'F_'
        
        if not args['lemmatizing']:
            file_prefix += 'N'
        
        file_prefix += 'L_'
        
        if not args['same_POS']:
            file_prefix += 'N'
        
        file_prefix += 'P_'
        file_prefix += str(args['n_timebags']) + '_'
        
        for (i, j) in args['bag_transitions']:
            file_prefix += '{}-{}_'.format(i, j)
        
        pickle_wn_PR_scores = \
            st.memetracker_subst_wn_PR_scores_pickle.format(file_prefix)
        pickle_wn_degrees = \
            st.memetracker_subst_wn_degrees_pickle.format(file_prefix)
        pickle_fa_PR_scores = \
            st.memetracker_subst_fa_PR_scores_pickle.format(file_prefix)
        
        # Check that the destinations don't already exist.
        
        st.check_file(pickle_wn_PR_scores)
        st.check_file(pickle_wn_degrees)
        st.check_file(pickle_fa_PR_scores)
        
        return {'wn_PR_scores': pickle_wn_PR_scores,
                'wn_degrees': pickle_wn_degrees,
                'fa_PR_scores': pickle_fa_PR_scores}
    
    def print_args(self, args):
        """Print the arguments to stdout."""
        print
        print 'Doing analysis with the following parameters:'
        print '  framing = {}'.format(args['framing'])
        print '  lemmatizing = {}'.format(args['lemmatizing'])
        print '  same_POS = {}'.format(args['same_POS'])
        print '  verbose = {}'.format(args['verbose'])
        print '  n_timebags = {}'.format(args['n_timebags'])
        print '  transitions = {}'.format(args['bag_transitions'])
    
    def load_data(self, framed):
        """Load the data from pickle files.
        
        Arguments:
          * framed: (boolean) load the framed or non-framed data
        
        Returns: a dict containing the various data structures loaded.
        
        """
        
        print
        print ('Connecting to redis server for cluster data, '
               'loading PageRank and degree data from pickle...'),
        
        if framed:
            clusters = rt.RedisReader(st.redis_mt_clusters_framed_pref)
        else:
            clusters = rt.RedisReader(st.redis_mt_clusters_pref)
        
        wn_PR = ps.load(st.wordnet_PR_scores_pickle)
        wn_degrees = ps.load(st.wordnet_degrees_pickle)
        fa_PR = ps.load(st.freeassociation_norms_PR_scores_pickle)
        
        print 'OK'
        
        return {'clusters': clusters, 'wn_PR': wn_PR,
                'wn_degrees': wn_degrees, 'fa_PR': fa_PR}
    
    def examine_substitutions(self, args, data):
        """Examine substitutions and retain only those we want.
        
        Arguments:
          * args: the dict of arguments, gotten from the command line or
                  manually set
          * data: the dict containing the data to be examined
        
        Returns: a dict containing two Nx2 numpy arrays, each one containing
                 the features (PR scores or degrees) of the substituted and
                 substitutant words from the substitutions that were kept
                 after filtering.
        
        Details:
          The method takes each Cluster (framed or not, depending on the
          'framing' argument), splits it into a number of TimeBags, then looks
          at the transitions between TimeBags defined by the 'bag_transitions'
          arguments in args: for each transition (e.g. TimeBag #0 to TimeBag
          #2), it takes the highest frequency string in the first TimeBag,
          gets all strings in the second TimeBag which are at
          hamming_word-distance == 1, and looks at any substitutions: when a
          substitution is found, depending on the arguments it can go through
          the following:
            * get excluded if both words (substituted and substitutant) aren't
              from the same grammatical category ('same_POS' argument)
            * the substituted and substitutant word can be lemmatized
              ('lemmatize' argument)
          Once that processing is done, the features of the substituted word
          and the new word are stored (if they exist in the features list).
        
        """
        
        print
        print 'Doing substitution analysis:'
        
        tagger = TreeTaggerTags(TAGLANG='en', TAGDIR=st.treetagger_TAGDIR,
                                TAGINENC='utf-8', TAGOUTENC='utf-8')
        
        # Results of the analysis
        
        wn_PR_scores = []
        wn_degrees = []
        fa_PR_scores = []
        n_stored_wn = 0
        n_stored_fa = 0
        n_all = 0
        
        # Progress info
        
        progress = 0
        n_clusters = len(data['clusters'])
        info_step = max(int(round(n_clusters / 100)), 1)
        
        for cl in data['clusters'].itervalues():
            
            # Progress info
            
            progress += 1
            
            if progress % info_step == 0:
                
                print '  {} % ({} / {} clusters)'.format(
                    int(round(100 * progress / n_clusters)),
                    progress, n_clusters)
            
            
            # Get timebags and examine transitions.
            
            tbgs = cl.build_timebags(args['n_timebags'])
            
            for i, j in args['bag_transitions']:
                
                # Highest freq string and its daughters
                # (sphere of hamming_word distance =1)
                
                smax = tbgs[i].max_freq_string.lower()
                smax_pos = tagger.Tags(smax)
                smax_tok = tagger.Tokenize(smax)
                daughters = [tbgs[j].strings[k].lower()
                             for k in tbgs[j].hamming_word_sphere(smax, 1)]
                
                for s in daughters:
                    
                    n_all += 1
                    
                    # Find the word that was changed.
                    
                    s_pos = tagger.Tags(s)
                    s_tok = tagger.Tokenize(s)
                    idx = np.where([w1 != w2 for (w1, w2) in
                                    zip(s_tok, smax_tok)])[0]
                    
                    
                    # Verbose info
                    
                    if args['verbose']:
                        
                        print
                        print ("***** SUBST (cl #{}) ***** '".format(cl.id) +
                               '{}/{}'.format(smax_tok[idx], smax_pos[idx]) +
                               "' -> '" + '{}/{}'.format(s_tok[idx],
                                                         s_pos[idx]) + "'")
                        print smax
                        print '=>'
                        print s
                        print
                    
                    
                    # Check the POS tags if asked to.
                    
                    if args['same_POS']:
                        
                        if s_pos[idx][:2] != smax_pos[idx][:2]:
                            
                            if args['verbose']:
                                
                                print 'Stored: NO (different POS)'
                                raw_input()
                            
                            break
                    
                    
                    # Lemmatize the words if asked to.
                    
                    if args['lemmatizing']:
                        
                        m1 = wn.morphy(smax_tok[idx])
                        if m1 != None:
                            lem1 = m1
                        else:
                            lem1 = smax_tok[idx]
                        
                        m2 = wn.morphy(s_tok[idx])
                        if m2 != None:
                            lem2 = m2
                        else:
                            lem2 = s_tok[idx]
                        
                        # Verbose info
                        
                        if args['verbose']:
                            print ("Lemmatized: '" + lem1 + "' -> '" +
                                   lem2 + "'")
                        
                    else:
                        
                        lem1 = smax_tok[idx]
                        lem2 = s_tok[idx]
                    
                    
                    # Exclude if this isn't really a substitution.
                    
                    if levenshtein(lem1, lem2) <= 1:
                        
                        # Verbose info
                        
                        if args['verbose']:
                            
                            print 'Stored: NO (not substitution)'
                            raw_input()
                        
                        break
                    
                    
                    # Look the words up in the WN features lists.
                    
                    try:
                        
                        wn_PR_scores.append([data['wn_PR'][lem1],
                                             data['wn_PR'][lem2]])
                        wn_degrees.append([data['wn_degrees'][lem1],
                                           data['wn_degrees'][lem2]])
                        n_stored_wn += 1
                        
                        # Verbose info
                        
                        if args['verbose']:
                            print 'Stored: wordnet YES'
                        
                    except KeyError:
                        
                        # Verbose info
                        
                        if args['verbose']:
                            print 'Stored: wordnet NO (not referenced)'
                    
                    
                    # Look the words up in the FA features lists.
                    
                    try:
                        
                        fa_PR_scores.append([data['fa_PR'][lem1],
                                             data['fa_PR'][lem2]])
                        n_stored_fa += 1
                        
                        # Verbose info
                        
                        if args['verbose']:
                            print 'Stored: freeass YES'
                        
                    except KeyError:
                        
                        # Verbose info
                        
                        if args['verbose']:
                            print 'Stored: freeass NO (not referenced)'
                    
                    
                    # Pause to read verbose info.
                    
                    if args['verbose']:
                        raw_input()
        
        
        print
        print 'Examined {} substitutions.'.format(n_all)
        print ('Stored {} substitutions with Wordnet '
               'scores').format(n_stored_wn)
        print ('Stored {} substitutions with Free Association '
               'scores').format(n_stored_fa)
        
        return {'wn_PR_scores': wn_PR_scores, 'wn_degrees': wn_degrees,
                'fa_PR_scores': fa_PR_scores}
    
    def save_results(self, files, results):
        """Save the analysis results to pickle files.
        
        Arguments:
          * files: the dict of filenames as given by 'get_save_files'
          * results: the dict of results as given by 'examine_substitutions'
        
        """
        
        print
        print 'Done. Saving data...',
        
        ps.save(np.array(results['wn_PR_scores']), files['wn_PR_scores'])
        ps.save(np.array(results['wn_degrees']), files['wn_degrees'])
        ps.save(np.array(results['fa_PR_scores']), files['fa_PR_scores'])
    
        print 'OK'
    
    def create_args_list(self, n_timebags_list):
        """Create a list of possible args dicts, according to requested
        timebag slicings.
        
        The resulting args all have framing, lemmatizing, and same_POS set to
        True. They only differ in the number of timebags to slice the clusters
        into, and which transition to examine.
        
        Arguments:
          * n_timebags_list: a list of integers, each one indicating how many
                             timebags the clusters are to be sliced into
        
        Returns:
          * args_list: a list of dicts, each one corresponding to a specific
                       n_timebags value and a specific transition between
                       timebags among those n_timebags. All possible
                       transitions are included.
        
        """
        
        args_list = []
        
        for n_timebags in n_timebags_list:
            
            for tr in build_timebag_transitions(n_timebags):
                
                args_list.append({'framing': True,
                                  'lemmatizing': True,
                                  'same_POS': True,
                                  'verbose': False,
                                  'n_timebags': n_timebags,
                                  'bag_transitions': [tr]})
        
        return args_list
    
    def analyze(self, args):
        """Load data, do the substitution analysis, and save results.
        
        Arguments:
          * args: the dict of args for the analysis
        
        """
        
        self.print_args(args)
        files = self.get_save_files(args)
        data = self.load_data(args['framing'])
        results = self.examine_substitutions(args, data)
        self.save_results(files, results)
    
    def analyze_all(self, n_timebags_list):
        """Run 'analyze' with various timebag slicings.
        
        The analysis is always done with framing, lemmatizing, and same_POS
        activated.
        
        Arguments:
          * n_timebags_list: a list of integers, each one indicating how many
                             timebags the clusters are to be sliced into
        
        """
        
        print
        print ('Starting substitution analysis, for timebag '
               'slicings {}').format(n_timebags_list)
        
        args_list = self.create_args_list(n_timebags_list)
        
        for args in args_list:
            self.analyze(args)
    
    def put_analyze(self, Q, args):
        """Put an analysis job in the queue."""
        Q.put(self.analyze(args))
    
    def analyze_all_mt(self, n_timebags_list):
        """Run 'analyze' with various timebag slicings, multi-threaded."""
        
        print
        print ('Starting multi-threaded substitution analysis, for timebag '
               'slicings {}').format(n_timebags_list)
        
        args_list = self.create_args_list(n_timebags_list)
        n_jobs = len(args_list)
        n_groups = int(np.ceil(n_jobs / self.n_proc))
        Q = Queue()
        
        print
        print ('Grouping {} jobs into {} groups of {} processes (except '
               'maybe for the last group).').format(n_jobs, n_groups,
                                                    self.n_proc)
        
        for i in range(n_groups):
            
            for j in range(i * self.n_proc,
                           min((i + 1) * self.n_proc, n_jobs)):
                
                thread = Process(target=self.put_analyze,
                                 args=(Q, args_list[j]))
                thread.daemon = True
                thread.start()
                
            for j in range(i * self.n_proc,
                           min((i + 1) * self.n_proc, n_jobs)):
                Q.get()
