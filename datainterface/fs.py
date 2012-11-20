import os
from warnings import warn


def check_folder(folder):
    """Check if folder exists; if not, create it and notify the user."""
    if not os.path.exists(folder):
        print "*** FS: '" + folder + "' does not exist. Creating it."
        os.makedirs(folder)


def check_file(filename, look_for_absent=False):
    """Check if filename already exists; if it does, raise an exception."""
    if os.path.exists(filename):

        if not look_for_absent:
            raise Exception(("File '" + filename + "' already exists! You should "
                             "sort this out first: I'm not going to overwrite "
                             'it. Aborting.'))
    else:

        if look_for_absent:
            raise Exception("File '" + filename + "' not found.")


def get_save_file(ma, readonly=False):
    """Get the filename where data is to be saved to or read from; check
    either that they don't already exist, or that they do exist.

    Arguments:
        * ma: a MiningArgs instance (= processed arguments from
                command line)

    Keyword arguments:
        * readonly: boolean specifying the behaviour for checking the files.
                    False means we want to be warned if the files already
                    exist, True means we want to be warned if the files
                    don't exist. Defaults to False.

    Returns: a dict of filenames corresponding to the data to save, or
                None if a check failed.

    """

    # Prevent circular imports
    import settings as st

    # Create the file prefix according to 'ma'.

    file_prefix = ''
    file_prefix += 'F{}_'.format(ma.ff)
    file_prefix += 'M{}_'.format(ma.model)
    file_prefix += 'S{}_'.format('yes' if ma.substrings else 'no')
    file_prefix += 'P{}_'.format(ma.POS)

    if ma.is_fixedslicing_model():
        file_prefix += 'N{}_'.format(ma.n_timebags)

    filename = st.mt_mining_substitutions_pickle.format(file_prefix)

    # Check that the destination doesn't already exist.

    try:
        check_file(filename, look_for_absent=readonly)

    except Exception, msg:

        if readonly:

            warn('{}: not found'.format(filename))
            return None

        else:

            if ma.resume:

                warn(('*** A file for parameters {} already exists, not '
                        'overwriting it. Skipping this whole '
                        'argset. ***').format(file_prefix))
                return None

            else:

                raise Exception(msg)

    return filename
