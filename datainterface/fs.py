import os
from warnings import warn


def check_folder(folder):
    """Check if folder exists; if not, create it and notify the user."""
    if not os.path.exists(folder):
        print "*** FS: '" + folder + "' does not exist. Creating it."
        os.makedirs(folder)


def check_file(filename, for_read=False):
    """Check if filename already exists; if it does, raise an exception."""
    if os.path.exists(filename):

        if not for_read:
            raise Exception(("File '" + filename + "' already exists! You should "
                             "sort this out first: I'm not going to overwrite "
                             'it. Aborting.'))
    else:

        if for_read:
            raise Exception("File '" + filename + "' not found.")

    return True


def get_filename(args):

    # Prevent circular imports
    import settings as st

    # Create the file prefix according to 'ma'.

    file_prefix = ''
    file_prefix += 'F{}_'.format(args.ff)
    file_prefix += 'M{}_'.format(args.model)
    file_prefix += 'S{}_'.format('yes' if args.substrings else 'no')
    file_prefix += 'P{}_'.format(args.POS)

    if args.is_fixedslicing_model():
        file_prefix += 'N{}_'.format(args.n_timebags)

    filename = st.mt_mining_substitutions_pickle.format(file_prefix)

    # Check that the destination doesn't already exist.
    try:
        # The file is for writing
        resume = args.resume
        for_read = False
    except AttributeError:
        # The file is for reading
        for_read = True

    try:
        check_file(filename, for_read=for_read)

    except Exception, msg:

        if for_read:

            warn('{}: not found'.format(filename))
            return None

        else:

            if resume:

                warn(('*** A file for parameters {} already exists, not '
                      'overwriting it. Skipping this whole '
                      'argset. ***').format(file_prefix))
                return None

            else:

                raise Exception(msg)

    return filename
