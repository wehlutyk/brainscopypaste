"""Load data from the MemeTracker dataset."""


from datetime import datetime
import re
from codecs import open
import logging
import pickle
from collections import defaultdict

import click
from progressbar import ProgressBar
import networkx as nx

from brainscopypaste.db import Session, Cluster, Quote, Url, save_by_copy
from brainscopypaste.utils import session_scope, execute_raw, cache
from brainscopypaste.features import SubstitutionFeaturesMixin
from brainscopypaste.conf import settings


logger = logging.getLogger(__name__)


def load_fa_features():
    logger.info('Computing FreeAssociation features')
    click.echo('Computing FreeAssociation features...')

    loader = FAFeatureLoader()
    degree = loader.degree()
    logger.debug('Saving FreeAssociation degree to pickle')
    with open(settings.DEGREE, 'wb') as f:
        pickle.dump(degree, f)

    pagerank = loader.pagerank()
    logger.debug('Saving FreeAssociation pagerank to pickle')
    with open(settings.PAGERANK, 'wb') as f:
        pickle.dump(pagerank, f)

    betweenness = loader.betweenness()
    logger.debug('Saving FreeAssociation betweenness to pickle')
    with open(settings.BETWEENNESS, 'wb') as f:
        pickle.dump(betweenness, f)

    clustering = loader.clustering()
    logger.debug('Saving FreeAssociation clustering to pickle')
    with open(settings.CLUSTERING, 'wb') as f:
        pickle.dump(clustering, f)

    click.secho('OK', fg='green', bold=True)
    logger.info('Done computing all FreeAssociation features')


def load_mt_frequency_and_tokens():
    logger.info('Computing memetracker frequencies and token list')
    click.echo('Computing MemeTracker frequencies and token list...')

    # See if we should count frequency of tokens or lemmas.
    source_type = SubstitutionFeaturesMixin.__features__['frequency']
    logger.info('Frequencies will be computed on %s', source_type)

    with session_scope() as session:
        quote_ids = session.query(Quote.id).filter(Quote.filtered.is_(True))

        # Check we have filtered quotes.
        if quote_ids.count() == 0:
            raise Exception('Found no filtered quotes, aborting.')
        quote_ids = [id for (id,) in quote_ids]

    # Compute frequencies and token list.
    frequencies = defaultdict(int)
    tokens = set()
    for quote_id in ProgressBar()(quote_ids):
        with session_scope() as session:
            quote = session.query(Quote).get(quote_id)
            tokens.update(quote.tokens)
            for word in getattr(quote, source_type):
                frequencies[word] += quote.frequency
    # Convert frequency back to a normal dict.
    frequencies = dict(frequencies)

    logger.debug('Saving memetracker frequencies to pickle')
    with open(settings.FREQUENCY, 'wb') as f:
        pickle.dump(frequencies, f)
    logger.debug('Saving memetracker token list to pickle')
    with open(settings.TOKENS, 'wb') as f:
        pickle.dump(tokens, f)

    click.secho('OK', fg='green', bold=True)
    logger.info('Done computing memetracker frequencies and token list')


class Parser:

    def _skip_header(self):
        for i in range(self.header_size):
            self._file.readline()


class FAFeatureLoader(Parser):

    header_size = 4

    @cache
    def _norms(self):
        """Parse the Appendix A files.

        After loading, `self.norms` is a dict containing, for each
        (lowercased) cue, a list of tuples. Each tuple represents a word
        referenced by the cue, and is in format `(word, ref, weight)`:
        `word` is the referenced word; `ref` is a boolean indicating
        if `word` has been normed or not; `weight` is the strength of
        the referencing.

        """

        logger.info('Loading FreeAssociation norms')

        norms = {}
        for filename in settings.FA_SOURCES:
            with open(filename, encoding='iso-8859-2') as self._file:

                self._skip_header()
                for line in self._file:
                    # Exit if we're at the end of the data.
                    if line[0] == '<':
                        break

                    # Parse our line.
                    linefields = line.split(', ')
                    w1 = linefields[0].lower()
                    w2 = linefields[1].lower()
                    ref = linefields[2].lower() == 'yes'
                    weight = float(linefields[5])

                    norm = (w2, ref, weight)
                    try:
                        norms[w1].append(norm)
                    except KeyError:
                        norms[w1] = [norm]

        logger.info('Loaded norms for %s words from FreeAssociation',
                    len(norms))
        return norms

    @cache
    def _norms_graph(self):
        logger.info('Computing FreeAssociation norms directed graph')
        graph = nx.DiGraph()
        graph.add_weighted_edges_from([(w1, w2, weight)
                                       for w1, norm in self._norms.items()
                                       for w2, _, weight in norm
                                       if weight != 0])
        return graph

    @cache
    def _inverse_norms_graph(self):
        logger.info('Computing FreeAssociation inverse norms directed graph')
        graph = nx.DiGraph()
        graph.add_weighted_edges_from(
            [(w1, w2, 1 / weight) for w1, w2, weight
             in self._norms_graph.edges_iter(data='weight')]
        )
        return graph

    @cache
    def _undirected_norms_graph(self):
        logger.info('Computing FreeAssociation norms undirected graph')
        graph = nx.Graph()
        for w1, w2, weight in self._norms_graph.edges_iter(data='weight'):
            if graph.has_edge(w1, w2):
                # Add to the existing weight instead of replacing it.
                weight += graph.edge[w1][w2]['weight']
            graph.add_edge(w1, w2, weight=weight)
        return graph

    @classmethod
    def _remove_zeros(self, feature):
        for word in list(feature.keys()):
            if feature[word] == 0:
                del feature[word]

    def degree(self):
        # Assumes a directed unweighted graph.
        logger.info('Computing FreeAssociation degree')
        degree = nx.in_degree_centrality(self._norms_graph)
        self._remove_zeros(degree)
        logger.info('Done computing FreeAssociation degree')
        return degree

    def pagerank(self):
        # Assumes a directed weighted graph.
        logger.info('Computing FreeAssociation pagerank')
        pagerank = nx.pagerank_scipy(self._norms_graph, max_iter=10000,
                                     tol=1e-15, weight='weight')
        self._remove_zeros(pagerank)
        logger.info('Done computing FreeAssociation pagerank')
        return pagerank

    def betweenness(self):
        # Assumes a directed weighted graph.
        logger.info('Computing FreeAssociation betweenness '
                    '(this might take a long time, e.g. 30 minutes)')
        betweenness = nx.betweenness_centrality(self._inverse_norms_graph,
                                                weight='weight')
        self._remove_zeros(betweenness)
        logger.info('Done computing FreeAssociation betweenness')
        return betweenness

    def clustering(self):
        # Assumes an undirected weighted graph.
        logger.info('Computing FreeAssociation clustering')
        clustering = nx.clustering(self._undirected_norms_graph,
                                   weight='weight')
        self._remove_zeros(clustering)
        logger.info('Done computing FreeAssociation clustering')
        return clustering


class MemeTrackerParser(Parser):

    """Parse the MemeTracker file into database."""

    # How many lines to skip at the beginning of the file.
    header_size = 6

    def __init__(self, filename, line_count, limit=None):
        """Setup progress printing."""

        self.filename = filename
        self.line_count = line_count
        self.limit = limit

        # Keep track of if we've already parsed or not.
        self.parsed = False

        # Keep track of current cluster and quote.
        self._cluster = None
        self._quote = None

    def parse(self):
        """Parse using the defined cluster-, quote-, and url-handlers."""

        logger.info('Parsing memetracker file')
        if self.limit is not None:
            logger.info('Parsing is limited to %s clusters', self.limit)

        click.echo('Parsing MemeTracker data file into database{}...'
                   .format('' if self.limit is None
                           else ' (limit={})'.format(self.limit)))

        if self.parsed:
            raise ValueError('Parser has already run')

        # +100 is some margin for ProgressBar.
        lines_left = self.line_count - self.header_size + 100
        with open(self.filename, 'rb', encoding='utf8') as self._file, \
                ProgressBar(max_value=lines_left,
                            redirect_stdout=True) as self._bar:
            self._parse()

        click.secho('OK', fg='green', bold=True)
        logger.info('Parsed %s clusters and %s quotes from memetracker file',
                    len(self._objects['clusters']),
                    len(self._objects['quotes']))

        # Save.
        logger.info('Saving parsed clusters to database')
        save_by_copy(**self._objects)
        self._objects = {'clusters': [], 'quotes': []}

        # Vacuum analyze.
        logger.info('Vacuuming and analyzing database')
        click.echo('Vacuuming and analyzing... ', nl=False)
        execute_raw(Session.kw['bind'], 'VACUUM ANALYZE')
        click.secho('OK', fg='green', bold=True)

        # And check.
        logger.info('Checking consistency of the file against the database')
        click.echo('Checking consistency...')
        self._check()

        # Don't do this twice.
        self.parsed = True
        click.secho('All done.', fg='green', bold=True)

    def _parse(self):

        # The first lines are not data.
        self._skip_header()

        # Initialize the parsing with the first line.
        self._cluster_line = self._file.readline()
        self._clusters_read = 0
        self._lines_read = 1
        self._bar.update(self._lines_read)

        # Results to be saved and checks to be done.
        self._objects = {'clusters': [], 'quotes': []}
        self._checks = {}

        while self._cluster_line is not None:
            logger.debug("Parsing new cluster ('%s')", self._cluster_line[:-1])
            self._parse_cluster_block()

    def _check(self):
        for id, check in ProgressBar()(self._checks.items()):
            logger.debug('Checking cluster #%s consistency', id)

            with session_scope() as session:
                # Check the cluster itself.
                cluster = session.query(Cluster).get(id)
                err_end = (' #{} does not match value'
                           ' in file').format(cluster.sid)
                if check['cluster']['size'] != cluster.size:
                    raise ValueError("Cluster size" + err_end)
                if check['cluster']['frequency'] != cluster.frequency:
                    raise ValueError("Cluster frequency" + err_end)

                # Check each quote.
                for quote in cluster.quotes:
                    quote_check = check['quotes'][quote.id]
                    err_end = (' #{} does not match value'
                               ' in file').format(quote.sid)
                    if quote_check['size'] != quote.size:
                        raise ValueError("Quote size" + err_end)
                    if quote_check['frequency'] != quote.frequency:
                        raise ValueError("Quote frequency" + err_end)

        self._checks = {}

    def _parse_cluster_block(self):
        # Check we have a cluster line and parse it.
        tipe, fields = self._parse_line(self._cluster_line)
        # If self._cluster_line stays None, _parse() stops.
        # So it's filled further down when we get to the next cluster
        # definition line (unless self.limit says we should read
        # only a subset of all clusters).
        self._cluster_line = None
        if tipe != 'cluster':
            raise ValueError("Our supposed cluster_line ('{}', line {}) "
                             "is not a cluster line!"
                             .format(self._cluster_line,
                                     self._lines_read + self.header_size))

        # Create the cluster.
        self._handle_cluster(fields)

        # Keep reading until the next cluster, or exhaustion.
        for line in self._file:
            self._lines_read += 1
            self._bar.update(self._lines_read)

            tipe, fields = self._parse_line(line)
            if tipe == 'cluster':
                break
            elif tipe == 'quote':
                self._handle_quote(fields)
            elif tipe == 'url':
                self._handle_url(fields)

        # If we just saw a new cluster, feed that new cluster_line
        # for the next cluster, unless asked to stop.
        self._clusters_read += 1
        if (tipe == 'cluster' and
                (self.limit is None or self._clusters_read < self.limit)):
            self._cluster_line = line

        # Clean up.
        self._cluster = None
        self._quote = None

    @classmethod
    def _parse_line(self, line):
        line0 = re.split(r'[\xa0\s+\t\r\n]+', line)
        if line0[0] != '':
            tipe = 'cluster'
        elif line[0] == '\t' and line[1] != '\t':
            tipe = 'quote'
        elif line[0] == '\t' and line[1] == '\t' and line[2] != '\t':
            tipe = 'url'
        else:
            tipe = None
        return tipe, re.split(r'[\t\r\n]', line)

    def _handle_cluster(self, fields):
        id = int(fields[3])
        self._cluster = Cluster(id=id, sid=id, filtered=False,
                                source='memetracker')
        self._objects['clusters'].append(self._cluster)

        # Save checks for later on.
        cluster_size = int(fields[0])
        cluster_frequency = int(fields[1])
        self._checks[self._cluster.id] = {
            'quotes': {},
            'cluster': {
                'size': cluster_size,
                'frequency': cluster_frequency
            }
        }

    def _handle_quote(self, fields):
        id = int(fields[4])
        self._quote = Quote(cluster_id=self._cluster.id, id=id, sid=id,
                            filtered=False, string=fields[3])
        self._objects['quotes'].append(self._quote)

        # Save checks for later on.
        quote_size = int(fields[2])
        quote_frequency = int(fields[1])
        self._checks[self._cluster.id]['quotes'][self._quote.id] = {
            'size': quote_size,
            'frequency': quote_frequency
        }

    def _handle_url(self, fields):
        timestamp = datetime.strptime(fields[2], '%Y-%m-%d %H:%M:%S')
        assert timestamp.tzinfo is None

        url = Url(timestamp=timestamp, frequency=int(fields[3]),
                  url_type=fields[4], url=fields[5])
        self._quote.add_url(url)
