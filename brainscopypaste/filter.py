from datetime import timedelta

import click
from progressbar import ProgressBar
from sqlalchemy import func
import numpy as np

from brainscopypaste.utils import langdetect, session_scope, execute_raw, cache
from brainscopypaste import settings


def filter_clusters(limit=None):
    # TODO: test
    from brainscopypaste.db import Session, Cluster, save_by_copy

    click.echo('Filtering all clusters{}...'
               .format('' if limit is None else ' (test run)'))

    # Check this isn't already done.
    with session_scope() as session:
        if session.query(Cluster)\
           .filter(Cluster.filtered.is_(True)).count() > 0:
            raise Exception('There are already some filtered '
                            'clusters, aborting.')

        query = session.query(Cluster.id)
        if limit is not None:
            query = query.limit(limit)
        cluster_ids = [id for (id,) in query]

    # Filter.
    objects = {'clusters': [], 'quotes': []}
    for cluster_id in ProgressBar()(cluster_ids):
        fcluster = session.query(Cluster).get(cluster_id).filter()
        if fcluster is not None:
            objects['clusters'].append(fcluster)
            objects['quotes'].extend(fcluster.quotes)
    click.secho('OK', fg='green', bold=True)

    # Save.
    save_by_copy(**objects)

    # Vacuum analyze.
    click.echo('Vacuuming and analyzing... ', nl=False)
    execute_raw(Session.kw['bind'], 'VACUUM ANALYZE')
    click.secho('OK', fg='green', bold=True)


class FilterMixin:

    @cache
    def filter_cluster_offset(self):
        # TODO: test
        from brainscopypaste.db import Cluster
        with session_scope() as session:
            maxid = session.query(func.max(Cluster.id)).scalar()
            return int(10 ** (np.floor(np.log10(maxid)) + 3))

    @cache
    def filter_quote_offset(self):
        # TODO: test
        from brainscopypaste.db import Quote
        with session_scope() as session:
            maxid = session.query(func.max(Quote.id)).scalar()
            return int(10 ** (np.floor(np.log10(maxid)) + 3))

    def filter(self):
        if self.filtered:
            raise ValueError('Cluster is already filtered')

        min_tokens = settings.mt_filter_min_tokens
        max_span = timedelta(days=settings.mt_filter_max_days)
        fcluster = self.clone(id=self.filter_cluster_offset + self.id,
                              filtered=True)

        # Examine each quote for min_tokens, max_days, and language.
        for quote in self.quotes:

            if quote.frequency == 0:
                continue

            if len(quote.tokens) < min_tokens:
                continue

            if quote.span > max_span:
                continue

            if langdetect(quote.string) != 'en':
                continue

            fquote = quote.clone(id=self.filter_quote_offset + quote.id,
                                 cluster_id=fcluster.id, filtered=True)
            fcluster.quotes.append(fquote)

        # If no quotes where kept, drop the whole cluster.
        if fcluster.size == 0:
            return

        # Finally, if the new cluster spans too many days, discard it.
        if fcluster.span > max_span:
            return

        return fcluster
