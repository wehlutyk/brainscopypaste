#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
