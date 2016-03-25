import logging
import importlib

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

    def override(self, name, value):
        if not name.isupper():
            raise ValueError('Setting names must be uppercase')
        if name not in dir(self.mod):
            raise ValueError('Unknown setting name')
        setattr(self, name, value)

    def reset(self):
        self._setup()


settings = Settings()
