from datetime import timedelta

from brainscopypaste.utils import langdetect
from brainscopypaste import settings


class FilterMixin:

    def filter(self):
        if self.filtered:
            raise ValueError('Cluster is already filtered')

        min_tokens = settings.mt_filter_min_tokens
        max_span = timedelta(days=settings.mt_filter_max_days)
        fcluster = self.clone(filtered=True)
        furls = []

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
            fquote.urls = [url.clone(quote_id=None, filtered=True)
                           for url in quote.urls]
            furls.extend(fquote.urls)

        # If no quotes where kept, drop the whole cluster.
        if fcluster.size == 0:
            return

        # Finally, if the new cluster spans too many days, discard it.
        furls = sorted(furls, key=lambda url: url.timestamp)
        if abs(furls[0].timestamp - furls[-1].timestamp) > max_span:
            return

        return fcluster
