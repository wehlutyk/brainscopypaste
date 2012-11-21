#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Mine the 1-word changes in the MemeTracker dataset.

"""


from mine.args import MiningArgs
from mine.substitutions import SubstitutionsMiner


if __name__ == '__main__':
    mining_args = MiningArgs()
    sm = SubstitutionsMiner(mining_args)
    sm.mine()
