"""Filter clusters and quotes to clean to MemeTracker dataset.

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
    pass


def filter_clusters(limit=None):
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
    return int(10 ** (np.floor(np.log10(id)) + 3))


@memoized
def filter_cluster_offset():
    from brainscopypaste.db import Cluster
    with session_scope() as session:
        maxid = session.query(func.max(Cluster.id)).scalar()
        return _top_id(maxid)


@memoized
def filter_quote_offset():
    from brainscopypaste.db import Quote
    with session_scope() as session:
        maxid = session.query(func.max(Quote.id)).scalar()
        return _top_id(maxid)


class ClusterFilterMixin:

    def filter(self):
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
