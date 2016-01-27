from datetime import timedelta

import click
from progressbar import ProgressBar

from brainscopypaste.utils import langdetect, session_scope
from brainscopypaste import settings


def filter_clusters(limit=None):
    from brainscopypaste.db import Cluster

    click.echo('Filtering all clusters{}...'
               .format('' if limit is None else ' (test run)'))

    # Check this isn't already done
    with session_scope() as session:
        if session.query(Cluster)\
           .filter(Cluster.filtered.is_(True)).count() > 0:
            raise Exception('There are already some filtered '
                            'clusters, aborting.')

        query = session.query(Cluster.id)
        if limit is not None:
            query = query.limit(limit)
        cluster_ids = [id for (id,) in query]

    for cluster_id in ProgressBar()(cluster_ids):
        with session_scope() as session:
            fcluster = session.query(Cluster).get(cluster_id).filter()
            if fcluster is not None:
                session.add(fcluster)

    click.secho('OK', fg='green', bold=True)


class FilterMixin:

    def filter(self):
        if self.filtered:
            raise ValueError('Cluster is already filtered')

        min_tokens = settings.mt_filter_min_tokens
        max_span = timedelta(days=settings.mt_filter_max_days)
        fcluster = self.clone(filtered=True)

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

            fquote = quote.clone(cluster_id=None, filtered=True)
            fcluster.quotes.append(fquote)

        # If no quotes where kept, drop the whole cluster.
        if fcluster.size == 0:
            return

        # Finally, if the new cluster spans too many days, discard it.
        print(fcluster.span)
        print(fcluster.urls)
        if fcluster.span > max_span:
            return

        return fcluster
