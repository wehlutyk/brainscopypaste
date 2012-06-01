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
from warnings import warn

from nltk.corpus import wordnet as wn
import numpy as np

import datastructure.memetracker as ds_mt
from linguistics.memetracker import levenshtein
from linguistics.treetagger import TreeTaggerTags
from linguistics.lang_detection import LangDetect
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


tagger = TreeTaggerTags(TAGLANG='en', TAGDIR=st.treetagger_TAGDIR,
                        TAGINENC='utf-8', TAGOUTENC='utf-8')

langdetecter = LangDetect()


def filter_cluster(cl, min_tokens):
    """Filter a cluster to keep only English quotes longer then 'min_tokens'.
    
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
    
    # If the root has less than wanted, filter the whole cluster.
    
    if (len(tagger.Tokenize(cl.root)) < min_tokens or
        langdetecter.detect(cl.root) != 'en'):
        return None
    
    # Else, examine each quote.
    
    filtered_quotes = {}
    
    for qt in cl.quotes.itervalues():
        
        if (len(tagger.Tokenize(qt.string)) >= min_tokens and
            langdetecter.detect(qt.string) == 'en'):
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
      * print_argset: print an argset to stdout
      * load_data: load the data from pickle files
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
    
    def get_save_files(self, argset):
        """Get the filenames where data is to be saved; check they don't
        already exist.
        
        Arguments:
          * argset: an argset of arguments (= processed arguments from
                    command line)
        
        Returns: a dict of filenames corresponding to the data to save.
        
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
        
        file_prefix += str(argset['n_timebags']) + '_'
        
        if argset['substitutions'] == 'tbg':
            file_prefix += ''.join(['{}-{}_'.format(i, j)
                                    for i, j in argset['bags']])
        else:
            file_prefix += ''.join(['{}_'.format(i) for i in argset['bags']])
        
        pickle_wn_PR_scores = \
            st.memetracker_subst_wn_PR_scores_pickle.format(file_prefix)
        pickle_wn_degrees = \
            st.memetracker_subst_wn_degrees_pickle.format(file_prefix)
        pickle_fa_PR_scores = \
            st.memetracker_subst_fa_PR_scores_pickle.format(file_prefix)
        
        pickle_wn_PR_scores_d = \
            st.memetracker_subst_wn_PR_scores_d_pickle.format(file_prefix)
        pickle_wn_degrees_d = \
            st.memetracker_subst_wn_degrees_d_pickle.format(file_prefix)
        pickle_fa_PR_scores_d = \
            st.memetracker_subst_fa_PR_scores_d_pickle.format(file_prefix)
        
        
        # Check that the destinations don't already exist.
        
        try:
            
            st.check_file(pickle_wn_PR_scores)
            st.check_file(pickle_wn_degrees)
            st.check_file(pickle_fa_PR_scores)
            st.check_file(pickle_wn_PR_scores_d)
            st.check_file(pickle_wn_degrees_d)
            st.check_file(pickle_fa_PR_scores_d)
        
        except Exception, msg:
            
            if argset['resume']:
                
                warn(('*** A file for parameters {} already exists, not '
                      'overwriting it. Skipping the whole '
                      'argset. ***').format(file_prefix))
                return None
            
            else:
                raise Exception(msg)
        
        return {'wn_PR_scores': pickle_wn_PR_scores,
                'wn_degrees': pickle_wn_degrees,
                'fa_PR_scores': pickle_fa_PR_scores,
                'wn_PR_scores_d': pickle_wn_PR_scores_d,
                'wn_degrees_d': pickle_wn_degrees_d,
                'fa_PR_scores_d': pickle_fa_PR_scores_d}
    
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
        print '  bags = {}'.format(argset['bags'])
    
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
        wn_PR = ps.load(st.wordnet_PR_scores_pickle.format(argset['POS']))
        wn_degrees = ps.load(st.wordnet_degrees_pickle.format(argset['POS']))
        fa_PR = ps.load(st.freeassociation_norms_PR_scores_pickle)
        
        print 'OK'
        
        return {'clusters': clusters, 'wn_PR': wn_PR,
                'wn_degrees': wn_degrees, 'fa_PR': fa_PR}
    
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
        
        tagger = TreeTaggerTags(TAGLANG='en', TAGDIR=st.treetagger_TAGDIR,
                                TAGINENC='utf-8', TAGOUTENC='utf-8')
        pos_wn_to_tt = {'a': 'J', 'n': 'N', 'v': 'V', 'r': 'R'}
        
        # If we're looking at substitutions from root, build fake transitions
        # that will be ignored further on.
        
        if argset['substitutions'] == 'tbg':
            bag_transitions = argset['bags']
        else:
            bag_transitions = [(0, i) for i in argset['bags']]
        
        # Results of the analysis
        
        wn_PR_scores = []
        wn_degrees = []
        fa_PR_scores = []
        
        wn_PR_scores_d = []
        wn_degrees_d = []
        fa_PR_scores_d = []
        
        n_stored_wn_PR = 0
        n_stored_wn_deg = 0
        n_stored_fa_PR = 0
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
            
            tbgs = cl.build_timebags(argset['n_timebags'])
            
            for i, j in bag_transitions:
                
                # Highest freq string and its daughters
                # (sphere of hamming_word distance =1)
                
                # Substitutions from timebags or from root
                
                if argset['substitutions'] == 'tbg':
                    smax = tbgs[i].max_freq_string.lower()
                else:
                    smax = cl.root

                smax_pos = tagger.Tags(smax)
                smax_tok = tagger.Tokenize(smax)
                
                # Substrings included or not
                
                if argset['substrings']:
                    daughters_mums = [(tbgs[j].strings[k].lower(), mum)
                                      for k, mum in
                                      tbgs[j].subhamming_word_sphere(smax, 1)]
                else:
                    smot = smax
                    smot_pos = smax_pos
                    smot_tok = smax_tok
                    daughters_mums = [(tbgs[j].strings[k].lower(), None)
                                      for k in
                                      tbgs[j].hamming_word_sphere(smot, 1)]
                
                for s, mum in daughters_mums:
                    
                    # Rebuild the mother thanks to info from subhamming
                    
                    if argset['substrings']:
                        
                        smot_tok = smax_tok[mum[0]:mum[0] + mum[1]]
                        smot_pos = smax_pos[mum[0]:mum[0] + mum[1]]
                        smot = ' '.join(smot_tok)
                    
                    # Pause to read verbose info.
                    
                    if argset['verbose']:
                        raw_input()
                    
                    n_all += 1
                    
                    
                    # Find the word that was changed.
                    
                    s_pos = tagger.Tags(s)
                    s_tok = tagger.Tokenize(s)
                    idx = np.where([w1 != w2 for (w1, w2) in
                                    zip(s_tok, smot_tok)])[0]
                    
                    # Verbose info
                    
                    if argset['verbose']:
                        
                        print
                        print ("***** SUBST (cl #{}) ***** '".format(cl.id) +
                               '{}/{}'.format(smot_tok[idx], smot_pos[idx]) +
                               "' -> '" + '{}/{}'.format(s_tok[idx],
                                                         s_pos[idx]) + "'")
                        print smot
                        print '=>'
                        print s
                        print
                    
                    
                    # Check the POS tags.
                    
                    if argset['POS'] == 'all':
                        
                        if s_pos[idx][0] != smot_pos[idx][0]:
                            
                            if argset['verbose']:
                                print 'Stored: NONE (different POS)'
                            
                            continue
                    
                    else:
                        
                        if (s_pos[idx][0] != pos_wn_to_tt[argset['POS']] or
                            smot_pos[idx][0] != pos_wn_to_tt[argset['POS']]):
                            
                            if argset['verbose']:
                                print 'Stored: NONE (wrong POS)'
                            
                            continue
                    
                    
                    # Lemmatize the words if asked to.
                    
                    if argset['lemmatizing']:
                        
                        m1 = wn.morphy(smot_tok[idx])
                        if m1 != None:
                            lem1 = m1
                        else:
                            lem1 = smot_tok[idx]
                        
                        m2 = wn.morphy(s_tok[idx])
                        if m2 != None:
                            lem2 = m2
                        else:
                            lem2 = s_tok[idx]
                        
                        # Verbose info
                        
                        if argset['verbose']:
                            print ("Lemmatized: '" + lem1 + "' -> '" +
                                   lem2 + "'")
                        
                    else:
                        
                        lem1 = smot_tok[idx]
                        lem2 = s_tok[idx]
                    
                    
                    # Exclude if this isn't really a substitution.
                    
                    if levenshtein(lem1, lem2) <= 1:
                        
                        # Verbose info
                        
                        if argset['verbose']:
                            print 'Stored: NONE (not substitution)'
                        
                        continue
                    
                    
                    # The details to be saved about the substitution
                    
                    details = {'cl_id': cl.id,
                               'smot': smot,
                               's': s,
                               'idx': idx,
                               'lem1': lem1,
                               'lem2': lem2,
                               'POS1': smot_pos[idx],
                               'POS2': s_pos[idx],
                               'bag_tr': (i, j),
                               'n_tbgs': argset['n_timebags']}
                    
                    
                    # Look the words up in the WN features lists.
                    
                    try:
                        
                        # Wordnet PageRank: take everything.
                        
                        wn_PR_scores.append([data['wn_PR'][lem1],
                                             data['wn_PR'][lem2]])
                        wn_PR_scores_d.append(details)
                        n_stored_wn_PR += 1
                        
                        if argset['verbose']:
                            print 'Stored: wordnet PR YES'
                        
                        wn_degrees.append([data['wn_degrees'][lem1],
                                           data['wn_degrees'][lem2]])
                        wn_degrees_d.append(details)
                        n_stored_wn_deg += 1
                        
                        if argset['verbose']:
                            print 'Stored: wordnet deg YES'
                        
                    except KeyError:
                        
                        # Verbose info
                        
                        if argset['verbose']:
                            
                            print 'Stored: wordnet PR NO (not referenced)'
                            print 'Stored: wordnet deg NO (not referenced)'
                    
                    except Exception:
                        
                        # Verbose info
                        
                        if argset['verbose']:
                            print 'Stored: wordnet deg NO (<= 2)'
                    
                    
                    # Look the words up in the FA features lists.
                    
                    try:
                        
                        fa_PR_scores.append([data['fa_PR'][lem1],
                                             data['fa_PR'][lem2]])
                        fa_PR_scores_d.append(details)
                        n_stored_fa_PR += 1
                        
                        # Verbose info
                        
                        if argset['verbose']:
                            print 'Stored: freeass YES'
                        
                    except KeyError:
                        
                        # Verbose info
                        
                        if argset['verbose']:
                            print 'Stored: freeass NO (not referenced)'
                    
                    except Exception:
                        
                        # Verbose info
                        
                        if argset['verbose']:
                            print 'Stored: freeass NO (<= damping)'
        
        
        print
        print 'Examined {} substitutions.'.format(n_all)
        print ('Stored {} substitutions with Wordnet PageRank '
               'scores').format(n_stored_wn_PR)
        print ('Stored {} substitutions with Wordnet degree '
               'scores').format(n_stored_wn_deg)
        print ('Stored {} substitutions with Free Association PageRank '
               'scores').format(n_stored_fa_PR)
        
        return {'wn_PR_scores': wn_PR_scores,
                'wn_degrees': wn_degrees,
                'fa_PR_scores': fa_PR_scores,
                'wn_PR_scores_d': wn_PR_scores_d,
                'wn_degrees_d': wn_degrees_d,
                'fa_PR_scores_d': fa_PR_scores_d}
    
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
        
        ps.save(np.array(results['wn_PR_scores_d']), files['wn_PR_scores_d'])
        ps.save(np.array(results['wn_degrees_d']), files['wn_degrees_d'])
        ps.save(np.array(results['fa_PR_scores_d']), files['fa_PR_scores_d'])
    
        print 'OK'
    
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
        
        for n_timebags in args.n_timebagss:
            
            for subsgs in args.substringss:
                
                for subtions in args.substitutionss:
                
                    if subtions == 'tbg':
                        transitions = \
                            build_timebag_transitions(int(n_timebags))
                    else:
                        transitions = range(1, int(n_timebags))
                    
                    for tr in transitions:
                        
                        for pos in args.POSs:
                            
                            for ff in args.ffs:
                                
                                argsets.append({'ff': ff,
                                            'lemmatizing': True,
                                            'substitutions': subtions,
                                            'substrings': bool(int(subsgs)),
                                            'POS': pos,
                                            'verbose': False,
                                            'n_timebags': int(n_timebags),
                                            'bags': [tr],
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
    
    def put_analyze(self, Q, argset):
        """Put an analysis job in the queue."""
        Q.put(self.analyze(argset))
    
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
                                 args=(Q, argsets[j]))
                thread.daemon = True
                thread.start()
                
            for j in range(i * self.n_proc,
                           min((i + 1) * self.n_proc, n_jobs)):
                Q.get()
