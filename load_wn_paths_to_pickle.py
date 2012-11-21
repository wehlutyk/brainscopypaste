import datainterface.picklesaver as ps
import linguistics.wn as l_wn
import datainterface.fs as di_fs
import settings as st


if __name__ == '__main__':

    # Load or compute the BCs for 'all'

    picklefile_all = st.wn_paths_pickle.format('all')
    try:
        di_fs.check_file(picklefile_all)
    except Exception:

        print
        print "The paths data for 'all' already exists, loading that data."
        loaded_all = ps.load(picklefile_all)
        paths_all = loaded_all['paths']
        distribution_all = loaded_all['distribution']

    else:

        print
        print ('*** Computing path lengths for all the lemmas in Wordnet '
               "(POS = 'all') ***")
        paths_all = l_wn.build_wn_paths('all')
        distribution_all = l_wn.build_paths_distribution(paths_all)

        print "*** Saving the path lengths and distribution to '" + picklefile_all + "'...",
        ps.save({'paths': paths_all, 'distribution': distribution_all},
                picklefile_all)
        print 'OK'

    # Then compute the other POSs

    POSs = st.mt_mining_POSs
    POSs.remove('all')
    for p in POSs:

        # Get the filename and check the destination doesn't exist.

        picklefile = st.wn_paths_pickle.format(p)

        try:
            di_fs.check_file(picklefile)
        except Exception:

            print picklefile + 'already exists, not overwriting it.'
            continue

        # Compute the BCs.

        print
        print ("*** Truncating the paths for 'all' to POS={} ***").format(p)

        paths = l_wn.truncate_wn_paths(paths_all, p)
        distribution = l_wn.build_paths_distribution(paths)

        # And save them.

        print "*** Saving the path lengths and distribution to '" + picklefile + "'...",
        ps.save({'paths': paths, 'distribution': distribution}, picklefile)
        print 'OK'
