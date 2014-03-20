#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Check for files and folders, build filenames and prefixes based on analysis
parameters."""


from __future__ import division

import os


def check_folder(folder):
    """Check if a folder exists or create it.

    If the folder gets created (because absent), information is logged
    (printed to stdout).

    Parameters
    ----------
    folder : string
        Path to the folder to check for.

    """

    if not os.path.exists(folder):
        print "*** FS: '" + folder + "' does not exist. Creating it."
        os.makedirs(folder)


def check_file(filename, for_read=False):
    """Check if a file already exists.

    Parameters
    ----------
    filename : string
        Path to the file to check for.
    for_read : bool, optional
        If ``True``, raise an exception if the file is absent. If ``False``,
        raise an exception if the file is present. Defaults to ``False``.

    Returns
    -------
    res : bool
        Always ``True`` (otherwise an exception will have been raised).

    """

    if os.path.exists(filename):

        if not for_read:
            raise Exception(("File '" + filename + "' already exists! "
                             "You should sort this out first: I'm not "
                             'going to overwrite it. Aborting.'))
    else:

        if for_read:
            raise Exception("File '" + filename + "' not found.")

    return True


def get_fileprefix(args):
    """Create a file prefix based on analysis parameters.

    File prefixes are used for saving and loading data to and from files for
    different argument sets. This function implements the defined way of
    naming files according to the argument set they stem from.

    Parameters
    ----------
    args : :class:`~baseargs.BaseArgs`
        The analysis parameters for which to create a file prefix.

    Returns
    -------
    file_prefix : string
        The prefix corresponding to the given `args`.

    """

    # Create the file prefix according to 'args'.

    try:

        file_prefix = ''
        file_prefix += 'F{}_'.format(args.ffs_text)
        file_prefix += 'M{}_'.format(args.models_text)
        file_prefix += 'S{}_'.format(args.substringss_text)
        file_prefix += 'P{}_'.format(args.POSs_text)

        try:
            file_prefix += 'D{}_'.format(args.timebag_size_text)
        except AttributeError:
            pass

    except AttributeError:

        file_prefix = ''
        file_prefix += 'F{}_'.format(args.ff)
        file_prefix += 'M{}_'.format(args.model)
        file_prefix += 'S{}_'.format('yes' if args.substrings else 'no')
        file_prefix += 'P{}_'.format(args.POS)

        if args.is_fixedslicing_model():
            file_prefix += 'D{}_'.format(args.timebag_size)

    return file_prefix


def get_filename(args):
    """Create a full mining data filename based on analysis parameters.

    Parameters
    ----------
    args : :class:`~baseargs.BaseArgs`
        The analysis Parameters for which to create a filename.

    Returns
    -------
    filename : string
        The full filename to store data for the given mining args.

    See Also
    --------
    get_fileprefix

    """

    # Prevent circular imports
    import settings as st

    file_prefix = get_fileprefix(args)
    filename = st.mt_mining_substitutions_pickle.format(file_prefix)

    return filename
