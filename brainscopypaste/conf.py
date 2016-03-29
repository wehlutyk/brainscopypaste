import logging
import importlib
from contextlib import contextmanager
import os
from tempfile import mkstemp

from brainscopypaste.utils import mkdirp


logger = logging.getLogger(__name__)


class Settings:

    def __init__(self):
        self.mod = importlib.import_module('brainscopypaste.settings')
        self._setup()
        for path in self.mod.paths_to_create:
            logger.debug("Checking for path '%s' to create", path)
            mkdirp(path)

    def _setup(self):
        for setting in dir(self.mod):
            if setting.isupper():
                setattr(self, setting, getattr(self.mod, setting))

    @contextmanager
    def override(self, *names_values):
        for name, value in names_values:
            self._override(name, value)
        yield
        self._setup()

    @contextmanager
    def file_override(self, *names):
        filepaths = [mkstemp()[1] for name in names]
        try:
            with self.override(*zip(names, filepaths)):
                yield
        finally:
            for filepath in filepaths:
                os.remove(filepath)

    def _override(self, name, value):
        if not name.isupper():
            raise ValueError('Setting names must be uppercase')
        if name not in dir(self.mod):
            raise ValueError('Unknown setting name')
        setattr(self, name, value)


settings = Settings()
