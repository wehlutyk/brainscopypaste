#!/usr/bin/env python
# -*- coding: utf-8 -*-


from mine.args import MultipleMiningArgs
from mine.substitutions import SubstitutionsMiner


if __name__ == '__main__':

    multiple_mining_args = MultipleMiningArgs()
    sm = SubstitutionsMiner()

    if multiple_mining_args.multi_thread:

        sm.mine_multiple_mt(multiple_mining_args)

    else:

        print
        print 'Deactivating multi-threading.'
        sm.mine_multiple(multiple_mining_args)
