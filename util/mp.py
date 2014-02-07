#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Hacky helper to have proper exception logging with multiprocessing.

This code is taken from http://stackoverflow.com/questions/6728236/exception-thrown-in-multiprocessing-pool-not-detected.

:class:`LoggingPool` defines a
:class:`multiprocessing.Pool <multiprocessing.pool.multiprocessing.Pool>` that
properly logs exceptions.

"""


from __future__ import division

import traceback
import logging
from multiprocessing import Pool
import multiprocessing


def error(msg, *args):
    """Shortcut to :mod:`multiprocessing`'s logger."""

    return multiprocessing.get_logger().error(msg, *args)


class LogExceptions(object):

    """A wrapper class that wraps a callable into a logging callable.

    An instance is itself callable, and wraps `callable` into a function
    that logs any exception to :mod:`multiprocessing`'s logger.

    Parameters
    ----------
    callable : callable
        The callable to wrap.

    """

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


class LoggingPool(object):

    """Mimic
    :class:`multiprocessing.Pool <multiprocessing.pool.multiprocessing.Pool>`'s
    behavior with additional logging capabilities.

    Raising exceptions inside
    :class:`multiprocessing.Pool <multiprocessing.pool.multiprocessing.Pool>`
    doesn't always get logged. To overcome this problem, this class wraps a
    :class:`multiprocessing.Pool <multiprocessing.pool.multiprocessing.Pool>`
    and provides the :meth:`map_async` and :meth:`apply_async` methods, that
    will properly log execptions raised in subprocesses.

    The constructor forwards arguments to
    :class:`multiprocessing.Pool <multiprocessing.pool.multiprocessing.Pool>`'s
    constructor.

    See Also
    --------
    multiprocessing.pool.multiprocessing.Pool, LogExceptions

    """

    def __init__(self, *args, **kwargs):
        multiprocessing.log_to_stderr(logging.DEBUG)
        self._pool = Pool(*args, **kwargs)

    def apply_async(self, func, args=(), kwds={}, callback=None):
        """Forward to
        :meth:`multiprocessing.Pool.apply_async <multiprocessing.pool.multiprocessing.Pool.apply_async>`,
        with wrapping for exception logging."""

        return self._pool.apply_async(LogExceptions(func), args,
                                      kwds, callback)

    def map_async(self, func, args=[], callback=None):
        """Forward to
        :meth:`multiprocessing.Pool.map_async <multiprocessing.pool.multiprocessing.Pool.map_async>`,
        with wrapping for exception logging."""

        return self._pool.map_async(LogExceptions(func), args, callback)
