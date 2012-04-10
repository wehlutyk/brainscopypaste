#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Do the MemeTracker substitution analysis with all possible parameter combinations."""

# Imports
import os


# Code
def _build_transitions(bag_indices, transitions):
    if len(bag_indices) > 1:
        transitions.extend([ (bag_indices[0], idx) for idx in bag_indices[1:] ])
        _build_transitions(bag_indices[1:], transitions)
    else:
        return []


def build_transitions(n_timebags):
    transitions = []
    _build_transitions(range(n_timebags), transitions)
    return transitions


if __name__ == '__main__':
    base_command = 'python memetracker_substitution_analysis.py \
--framing {fra} --lemmatizing {lem} --synonyms {syn} --ntimebags {ntb} {trs}'
    for lemmatizing in [0, 1]:
        for framing in [0, 1]:
            for synonyms_only in [0, 1]:
                for n_timebags in [2, 3]:
                    for (b1, b2) in build_transitions(n_timebags):
                        transition_text = '{}-{}'.format(b1, b2)
                        os.system(base_command.format(fra=framing, \
                                                      lem=lemmatizing, \
                                                      syn=synonyms_only, \
                                                      ntb=n_timebags, \
                                                      trs=transition_text))
