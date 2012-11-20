import traceback
import logging
from multiprocessing import Pool
import multiprocessing

# Shortcut to multiprocessing's logger
def error(msg, *args):
    return multiprocessing.get_logger().error(msg, *args)

class LogExceptions(object):

    def __init__(self, callable):
        self.__callable = callable
        return

    def __call__(self, *args, **kwargs):
        try:
            result = self.__callable(*args, **kwargs)

        except Exception as e:
            # Here we add some debugging help. If multiprocessing's
            # debugging is on, it will arrange to log the traceback
            error(traceback.format_exc())
            # Re-raise the original exception so the Pool worker can
            # clean up
            raise e

        # It was fine, give a normal answer
        return result
    pass

class LoggingPool(object):

    def __init__(self, *args, **kwargs):
        multiprocessing.log_to_stderr(logging.DEBUG)
        self._pool = Pool(*args, **kwargs)

    def apply_async(self, func, args=(), kwds={}, callback=None):
        return self._pool.apply_async(LogExceptions(func), args, kwds, callback)

    def map_async(self, func, args=[], callback=None):
        return self._pool.map_async(LogExceptions(func), args, callback)
