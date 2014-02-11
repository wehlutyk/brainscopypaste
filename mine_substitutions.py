#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Mine the 1-word changes in the MemeTracker dataset, with arguments defined
by a set of :class:`mine.args.MiningArgs`.

This script is meant to be used as a command line program. It will mine for
substitutions in the dataset according to provided arguments, and save the
results as pickle files. These results can then be later analyzed and
visualized with the :mod:`analyze_substitutions` and
:mod:`analyze_substitutions_multiple` scripts.

Run ``python mine_substitutions.py --help`` for more details on the arguments.

"""


from __future__ import division

from mine.args import MiningArgs
from mine.substitutions import SubstitutionsMiner


if __name__ == '__main__':
    mining_args = MiningArgs()
    sm = SubstitutionsMiner(mining_args)
    sm.mine()
