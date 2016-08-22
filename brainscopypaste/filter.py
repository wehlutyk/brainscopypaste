"""Filter clusters and quotes to clean to MemeTracker dataset.

This module defines the :class:`ClusterFilterMixin` mixin which adds filtering
capabilities to :class:`~.db.Cluster`, and the :func:`filter_clusters` function
which uses that mixin to filter the whole MemeTracker dataset. A few other
utility functions are also defined.

"""


from datetime import timedelta
import logging

import click
from progressbar import ProgressBar
from sqlalchemy import func
import numpy as np

from brainscopypaste.utils import (langdetect, session_scope, execute_raw,
                                   memoized)
from brainscopypaste.conf import settings


logger = logging.getLogger(__name__)


class AlreadyFiltered(Exception):
    """Exception raised when trying to filter a dataset that has already been
    filtered."""


def filter_clusters(limit=None):
    """Filter the whole MemeTracker dataset by copying all valid
    :class:`~.db.Cluster`\ s and :class:`~.db.Quote`\ s and setting their
    `filtered` attributes to `True`.

    Iterate through all the MemeTracker :class:`~.db.Cluster`\ s, and filter
    each of them to see if it's worth keeping. If a :class:`~.db.Cluster` is to
    be kept, the function creates a copy of it and all of its kept
    :class:`~.db.Quote`\ s, marking them as filtered. Progress of this
    operation is printed to stdout.

    Once the operation finishes, a VACUUM and an ANALYZE operation are run on
    the database so that it recomputes its optimisations.

    Parameters
    ----------
    limit : int, optional
        If not `None`, stop filtering after `limit` clusters have been seen
        (useful for testing purposes).

    Raises
    ------
    AlreadyFiltered
        If there are already some filtered :class:`~.db.Cluster`\ s or
        :class:`~.db.Quote`\ s stored in the database (indicating another
        filtering operation has already been completed, or started and
        aborted).

    """

    from brainscopypaste.db import Session, Cluster, save_by_copy

    logger.info('Filtering memetracker clusters')
    if limit is not None:
        logger.info('Filtering is limited to %s clusters', limit)

    click.echo('Filtering all clusters{}...'
               .format('' if limit is None else ' (limit={})'.format(limit)))

    # Check this isn't already done.
    with session_scope() as session:

        if session.query(Cluster)\
           .filter(Cluster.filtered.is_(True)).count() > 0:
            raise AlreadyFiltered('There are already some filtered '
                                  'clusters, aborting.')

        query = session.query(Cluster.id)
        if limit is not None:
            query = query.limit(limit)
        cluster_ids = [id for (id,) in query]

    logger.info('Got %s clusters to filter', len(cluster_ids))

    # Filter.
    objects = {'clusters': [], 'quotes': []}

    for cluster_id in ProgressBar()(cluster_ids):
        with session_scope() as session:

            cluster = session.query(Cluster).get(cluster_id)
            fcluster = cluster.filter()

            if fcluster is not None:
                logger.debug('Cluster #%s is kept with %s quotes',
                             cluster.sid, fcluster.size)
                objects['clusters'].append(fcluster)
                objects['quotes'].extend(fcluster.quotes)
            else:
                logger.debug('Cluster #%s is dropped', cluster.sid)

    click.secho('OK', fg='green', bold=True)
    logger.info('Kept %s clusters and %s quotes after filtering',
                len(objects['clusters']), len(objects['quotes']))

    # Save.
    logger.info('Saving filtered clusters to database')
    save_by_copy(**objects)

    # Vacuum analyze.
    logger.info('Vacuuming and analyzing database')
    click.echo('Vacuuming and analyzing... ', nl=False)
    execute_raw(Session.kw['bind'], 'VACUUM ANALYZE')
    click.secho('OK', fg='green', bold=True)


def _top_id(id):
    """Get the smallest power of ten three orders of magnitude greater than
    `id`.

    Used to compute :func:`filter_cluster_offset` and
    :func:`filter_quote_offset`.

    """

    return int(10 ** (np.floor(np.log10(id)) + 3))


@memoized
def filter_cluster_offset():
    """Get the offset to add to filtered :class:`~.db.Cluster` ids.

    A filtered :class:`~.db.Cluster`'s id will be its original
    :class:`~.db.Cluster`'s id plus this offset.  The function is
    :func:`~.utils.memoized` since it is called so often.

    """

    from brainscopypaste.db import Cluster
    with session_scope() as session:
        maxid = session.query(func.max(Cluster.id)).scalar()
        return _top_id(maxid)


@memoized
def filter_quote_offset():
    """Get the offset to add to filtered :class:`~.db.Quote` ids.

    A filtered :class:`~.db.Quote`'s id will be its original
    :class:`~.db.Quote`'s id plus this offset.  The function is
    :func:`~.utils.memoized` since it is called so often.

    """

    from brainscopypaste.db import Quote
    with session_scope() as session:
        maxid = session.query(func.max(Quote.id)).scalar()
        return _top_id(maxid)


class ClusterFilterMixin:

    """Mixin for :class:`~.db.Cluster`\ s adding the :meth:`filter` method used
    in :func:`filter_clusters`."""

    def filter(self):
        """Filter this :class:`~.db.Cluster` and its children
        :class:`~.db.Quote`\ s to see if they're worth keeping.

        First, iterate through all the children :class:`~.db.Quote`\ s of the
        cluster, seeing if each one of them is worth keeping. A
        :class:`~.db.Quote` is discarded if it has no urls, less than
        :data:`~.settings.MT_FILTER_MIN_TOKENS`, spans longer than
        :data:`~.settings.MT_FILTER_MAX_DAYS`, or is not in English. Any
        :class:`~.db.Quote` that has none of those problems will be kept.

        If after this filtering there are no :class:`~.db.Quote`\ s left, or
        the :class:`~.db.Cluster` made of the remaining :class:`~.db.Quote`\ s
        still spans longer than :data:`~.settings.MT_FILTER_MAX_DAYS`, the
        cluster and all its quotes will be discarded and `None` is returned.
        If not, a new :class:`~.db.Cluster` is created with `cluster.filtered =
        True` and `cluster.id = original_cluster.id +`
        :func:`filter_cluster_offset`. That new cluster points to copies of all
        the kept :class:`~.db.Quote`\ s, with `quote.filtered = True` and
        `quote.id = original_quote.id +` :func:`filter_quote_offset`. All those
        models (new cluster and new quotes) should later be saved to the
        database (the method does not do it for you), e.g. by running this
        method inside a :func:`~.utils.session_scope`.

        Returns
        -------
        cluster : :class:`~.db.Cluster` or None
            The filtered cluster pointing to filtered quotes, or `None` if it
            is to be discarded.

        Raises
        ------
        AlreadyFiltered
            If this cluster is already filtered (i.e.
            :attr:`~.db.Cluster.filtered` is `True`).

        """

        if self.filtered:
            raise AlreadyFiltered('Cluster is already filtered')

        min_tokens = settings.MT_FILTER_MIN_TOKENS
        max_span = timedelta(days=settings.MT_FILTER_MAX_DAYS)
        fcluster = self.clone(id=filter_cluster_offset() + self.id,
                              filtered=True)

        # Examine each quote for min_tokens, max_days, and language.
        for quote in self.quotes:

            if quote.frequency == 0:
                logger.debug('Dropping quote #%s (cluster #%s): '
                             'no urls', quote.sid, self.sid)
                continue

            if len(quote.tokens) < min_tokens:
                logger.debug('Dropping quote #%s (cluster #%s): '
                             'not enough tokens', quote.sid, self.sid)
                continue

            if quote.span > max_span:
                logger.debug('Dropping quote #%s (cluster #%s): '
                             'span too big', quote.sid, self.sid)
                continue

            if langdetect(quote.string) != 'en':
                logger.debug('Dropping quote #%s (cluster #%s): '
                             'not English', quote.sid, self.sid)
                continue

            logger.debug('Keeping quote #%s (cluster #%s)',
                         quote.sid, self.sid)
            fquote = quote.clone(id=filter_quote_offset() + quote.id,
                                 cluster_id=fcluster.id, filtered=True)
            fcluster.quotes.append(fquote)

        # If no quotes where kept, drop the whole cluster.
        if fcluster.size == 0:
            logger.debug('Dropping cluster #%s: no quotes left', self.sid)
            return

        # Finally, if the new cluster spans too many days, discard it.
        if fcluster.span > max_span:
            logger.debug('Dropping cluster #%s: span too big', self.sid)
            return

        logger.debug('Keeping cluster #%s after filtering', self.sid)
        return fcluster
