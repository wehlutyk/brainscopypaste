#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Mine the 1-word changes in the MemeTracker dataset, with multiple sets of
arguments defined by a set of :class:`mine.args.MultipleMiningArgs`.

This script is meant to be used as a command line program. It will mine for
substitutions in the dataset according to provided arguments, and save the
results as pickle files. It is mainly used as a parallel version of
:mod:`mine_substitutions`, allowing to mine for a large number of combinations
of arguments in one go, while multithreading independent mining threads. The
results can then be later analyzed and visualized with the
:mod:`analyze_substitutions` and :mod:`analyze_substitutions_multiple` scripts.

Run ``python mine_substitutions_multiple.py --help`` for more details on the
arguments.

"""


from __future__ import division

from mine.args import MultipleMiningArgs
from mine.substitutions import mine_multiple, mine_multiple_mt


if __name__ == '__main__':

    multiple_mining_args = MultipleMiningArgs()

    if multiple_mining_args.multi_thread:

        mine_multiple_mt(multiple_mining_args)

    else:

        print
        print 'Deactivating multi-threading.'
        mine_multiple(multiple_mining_args)
