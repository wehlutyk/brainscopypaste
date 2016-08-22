"""Manage settings from the :mod:`.settings` module, allowing overriding of
some values.

Use the :data:`settings` class instance from this module to access settings
from any other module: ``from brainscopypaste.conf import settings``. Note that
only uppercase variables from the :mod:`.settings` module are taken into
account, the rest is ignored.

"""


import logging
import importlib
from contextlib import contextmanager
import os
from tempfile import mkstemp

from brainscopypaste.utils import mkdirp


logger = logging.getLogger(__name__)


class Settings:

    """Hold all settings for the analysis, managing and proxying access to the
    :mod:`.settings` module.

    Only uppercase variables from the :mod:`.settings` module are taken into
    account, the rest is ignored. This class also lets you override values with
    a context manager to make testing easier. See the :meth:`override` and
    :meth:`file_override` methods for more details.

    Use the :data:`settings` instance of this class to access a singleton
    version of the settings for the whole analysis. Overridden values then
    appear overridden to all other modules (i.e. for all accesses) until the
    context manager is closed.

    """

    def __init__(self):
        """Import the :mod:`.settings` module and check for folders to
        create."""

        self.mod = importlib.import_module('brainscopypaste.settings')
        self._setup()
        for path in self.mod.paths_to_create:
            logger.debug("Checking for path '%s' to create", path)
            mkdirp(path)

    def _setup(self):
        """Set uppercase variables from the :mod:`.settings` module as
        attributes on this instance."""

        for setting in dir(self.mod):
            if setting.isupper():
                setattr(self, setting, getattr(self.mod, setting))

    @contextmanager
    def override(self, *names_values):
        """Context manager that overrides setting values for the duration of
        the context.

        Use this method to override one or several setting values for a block
        of code, then have those settings go back to their default value. Very
        useful when writing tests.

        Parameters
        ----------
        names_values : list of tuples
            List of `(name, value)` tuples defining which settings to override
            with what value. Setting names must already exist (you can't use
            this to create a new entry).

        Raises
        ------
        ValueError
            If any of the `name` values in `names_values` is not an uppercase
            string or is not a known setting name.

        See Also
        --------
        file_override

        Examples
        --------
        Override MemeTracker filter settings for the duration of a test:

        >>> from brainscopypaste.conf import settings
        >>> with settings.override(('MT_FILTER_MIN_TOKENS', 2),
        ...                        ('MT_FILTER_MAX_DAYS, 50)):
        ...     # Here: some test code using the overridden settings.
        >>> # `settings` is back to default here.

        """

        for name, value in names_values:
            self._override(name, value)
        try:
            yield
        finally:
            self._setup()

    @contextmanager
    def file_override(self, *names):
        """Context manager that overrides a file setting by pointing it to an
        empty temporary file for the duration of the context.

        Some values in the :mod:`.settings` module are file paths, and you
        might want to easily override the `contents` of that file for a block
        of code. This method lets you do just that: it will create a temporary
        file for a setting you wish to override, point that setting to the new
        empty file, and clean up once the context closes. This is a shortcut
        for :meth:`override` when working on files whose contents you want to
        override.

        Parameters
        ----------
        names : list of str
            List of setting names you want to override with temporary files.

        Raises
        ------
        ValueError
            If any member of `names` is not an uppercase string or is not a
            known setting name.

        See Also
        --------
        override

        Examples
        --------
        Override the Age-of-Acquisition source file to e.g. test code that
        imports it as a word feature:

        >>> from brainscopypaste.conf import settings
        >>> with settings.file_override('AOA'):
        ...    with open(settings.AOA, 'w') as aoa:
        ...        # Write test content to the temporary AOA file.
        ...    # Test your code on the temporary AOA content.
        >>> # `settings.AOA` is back to default here.

        """

        filepaths = [mkstemp()[1] for name in names]
        try:
            with self.override(*zip(names, filepaths)):
                yield
        finally:
            for filepath in filepaths:
                os.remove(filepath)

    def _override(self, name, value):
        """Override `name` with `value`, after some checks.

        The method checks that `name` is an uppercase string, and that it
        exists in the known settings. Use this when writing a context manager
        that wraps the operation in try/finally blocks, then restores the
        default behaviour.

        Parameters
        ----------
        name : str
            Uppercase string denoting a known setting to be overridden.
        value : object
            Value to replace the setting with.

        Raises
        ------
        ValueError
            If `name` is not an uppercase string or is not a known setting
            name.

        """

        if not name.isupper():
            raise ValueError('Setting names must be uppercase')
        if name not in dir(self.mod):
            raise ValueError('Unknown setting name')
        setattr(self, name, value)


#: Instance of the :class:`Settings` class that should be used to access
#: settings. See that class's documentation for more information.
settings = Settings()
