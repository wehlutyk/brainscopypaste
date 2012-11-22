import datainterface.picklesaver as ps
import linguistics.wn as l_wn
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Load or compute the BCs for 'all'

    picklefile = st.wn_lengths_pickle

    di_fs.check_file(picklefile)

    print
    print '*** Computing path lengths ***'
    lengths_detail = l_wn.build_wn_paths()

    print '*** Computing path length distribution ***'
    distribution = l_wn.build_wn_paths_distribution(lengths_detail)

    print "*** Saving the path length distribution to '" + picklefile + "'...",
    ps.save(distribution, picklefile)
    print 'OK'
