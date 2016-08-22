"""Load data from various datasets.

This module defines functions and classes to load and parse dataset files.
:func:`load_fa_features` loads Free Association features (using
:class:`FAFeatureLoader`) and :func:`load_mt_frequency_and_tokens` loads
MemeTracker features. Both save their computed features to pickle files for
later use in analyses. :class:`MemeTrackerParser` parses and loads the whole
MemeTracker dataset into the database and is used by :mod:`.cli`.

"""


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
    """Load the Free Association dataset and save all its computed features to
    pickle files.

    FA degree, pagerank, betweenness, and clustering are computed using the
    :class:`FAFeatureLoader` class, and saved respectively to
    :data:`~.settings.DEGREE`, :data:`~.settings.PAGERANK`,
    :data:`~.settings.BETWEENNESS` and :data:`~.settings.CLUSTERING`. Progress
    is printed to stdout.

    """

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
    """Compute MemeTracker frequency codings and the list of available tokens.

    Iterate through the whole MemeTracker dataset loaded into the database to
    count word frequency and make a list of tokens encountered. Frequency
    codings are then saved to :data:`~.settings.FREQUENCY`, and the list of
    tokens is saved to :data:`~.settings.TOKENS`. The MemeTracker dataset must
    have been loaded and filtered previously, or an excetion will be raised
    (see :ref:`usage` or :mod:`.cli` for more about that). Progress is printed
    to stdout.

    """

    logger.info('Computing memetracker frequencies and token list')
    click.echo('Computing MemeTracker frequencies and token list...')

    # See if we should count frequency of tokens or lemmas.
    source_type, _ = SubstitutionFeaturesMixin.__features__['frequency']
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

    """Mixin for file parsers providing the :meth:`_skip_header` method.

    Used by :class:`FAFeatureLoader` and :class:`MemeTrackerParser`.

    """

    def _skip_header(self):
        """Skip `self.header_size` lines in the file `self._file`."""

        for i in range(self.header_size):
            self._file.readline()


class FAFeatureLoader(Parser):

    """Loader for the Free Association dataset and features.

    This class defines a method to load the FA norms (:meth:`_norms`), utility
    methods to compute the different variants of graphs that can represent the
    norms (:meth:`_norms_graph`, :meth:`_inverse_norms_graph`, and
    :meth:`_undirected_norms_graph`) or to help feature computation
    (:meth:`_remove_zeros`), and public methods that compute features on the FA
    data (:meth:`degree`, :meth:`pagerank`, :meth:`betweenness`, and
    :meth:`clustering`). Use a single class instance to compute all FA
    features.

    """

    #: Size (in lines) of the header in files to be parsed.
    header_size = 4

    @cache
    def _norms(self):
        """Parse the Free Association Appendix A files into `self.norms`.

        After loading, `self.norms` is a dict containing, for each
        (lowercased) cue, a list of tuples. Each tuple represents a word
        referenced by the cue, and is in format `(word, ref, weight)`:
        `word` is the referenced word; `ref` is a boolean indicating
        if `word` has been normed or not; `weight` is the strength of
        the referencing.

        :func:`~.utils.memoized` for performance of the class.

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
        """Get the Free Association weighted directed graph.

        :func:`~.utils.memoized` for performance of the class.

        Returns
        -------
        :func:`networkx.DiGraph`
            The FA weighted directed graph.

        """

        logger.info('Computing FreeAssociation norms directed graph')
        graph = nx.DiGraph()
        graph.add_weighted_edges_from([(w1, w2, weight)
                                       for w1, norm in self._norms.items()
                                       for w2, _, weight in norm
                                       if weight != 0])
        return graph

    @cache
    def _inverse_norms_graph(self):
        """Get the Free Association directed graph with inverted weights.

        This graph is useful for computing e.g. :meth:`betweenness`, where link
        strength should be considered an inverse cost (i.e. a stronger link is
        easier to cross, instead of harder).

        :func:`~.utils.memoized` for performance of the class.

        Returns
        -------
        :func:`networkx.DiGraph`
            The FA inversely weighted directed graph.

        """

        logger.info('Computing FreeAssociation inverse norms directed graph')
        graph = nx.DiGraph()
        graph.add_weighted_edges_from(
            [(w1, w2, 1 / weight) for w1, w2, weight
             in self._norms_graph.edges_iter(data='weight')]
        )
        return graph

    @cache
    def _undirected_norms_graph(self):
        """Get the Free Association weighted undirected graph.

        When a pair of words is connected in both directions, the undirected
        link between the two words receives the sum of the two directed link
        weights. This is used to compute e.g. :meth:`clustering`, which is
        defined on the undirected (but weighted) FA graph.

        :func:`~.utils.memoized` for performance of the class.

        Returns
        -------
        :func:`networkx.Graph`
            The FA weighted undirected graph.

        """

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
        """Remove key-value pairs where value is zero, in dict `feature`.

        Modifies the provided `feature` dict, and does not return anything.

        Parameters
        ----------
        feature : dict
            Any association of key-value pairs where values are numbers.
            Usually a dict of words to feature values.

        """

        for word in list(feature.keys()):
            if feature[word] == 0:
                del feature[word]

    def degree(self):
        """Compute in-degree centrality for words coded by Free Association.

        Returns
        -------
        degree : dict
            The association of each word to its in-degree. Each incoming link
            counts as 1 (i.e. link weights are ignored). Words with zero
            incoming links are removed from the dict.

        """

        # Assumes a directed unweighted graph.
        logger.info('Computing FreeAssociation degree')
        degree = nx.in_degree_centrality(self._norms_graph)
        self._remove_zeros(degree)
        logger.info('Done computing FreeAssociation degree')
        return degree

    def pagerank(self):
        """Compute pagerank centrality for words coded by Free Association.

        Returns
        -------
        pagerank : dict
            The association of each word to its pagerank. FA link weights are
            taken into account in the computation. Words with pagerank zero are
            removed from the dict.

        """

        # Assumes a directed weighted graph.
        logger.info('Computing FreeAssociation pagerank')
        pagerank = nx.pagerank_scipy(self._norms_graph, max_iter=10000,
                                     tol=1e-15, weight='weight')
        self._remove_zeros(pagerank)
        logger.info('Done computing FreeAssociation pagerank')
        return pagerank

    def betweenness(self):
        """Compute betweenness centrality for words coded by Free Association.

        Returns
        -------
        betweenness : dict
            The association of each word to its betweenness centrality. FA link
            weights are considered as inverse cost in the computation (i.e. a
            stronger link is easier to cross). Words with betweenness zero are
            removed from the dict.

        """

        # Assumes a directed weighted graph.
        logger.info('Computing FreeAssociation betweenness '
                    '(this might take a long time, e.g. 30 minutes)')
        betweenness = nx.betweenness_centrality(self._inverse_norms_graph,
                                                weight='weight')
        self._remove_zeros(betweenness)
        logger.info('Done computing FreeAssociation betweenness')
        return betweenness

    def clustering(self):
        """Compute clustering coefficient for words coded by Free Association.

        Returns
        -------
        clustering : dict
            The association of each word to its clustering coefficient. FA link
            weights are taken into account in the computation, but direction of
            links is ignored (if words are connected in both directions, the
            link weights are added together). Words with clustering coefficient
            zero are removed from the dict.

        """

        # Assumes an undirected weighted graph.
        logger.info('Computing FreeAssociation clustering')
        clustering = nx.clustering(self._undirected_norms_graph,
                                   weight='weight')
        self._remove_zeros(clustering)
        logger.info('Done computing FreeAssociation clustering')
        return clustering


class MemeTrackerParser(Parser):

    """Parse the MemeTracker dataset into the database.

    After initialisation, the :meth:`parse` method does all the job. Its
    internal work is done by the utility methods :meth:`_parse`,
    :meth:`_parse_cluster_block` and :meth:`_parse_line` (for actual parsing),
    :meth:`_handle_cluster`, :meth:`_handle_quote` and :meth:`_handle_url` (for
    parsed data handling), and :meth:`_check` (for consistency checking).

    Parameters
    ----------
    filename : str
        Path to the MemeTracker dataset file to parse.
    line_count : int
        Number of lines in `filename`, to help in showing a progress bar.
        Should be computed beforehand with e.g. ``wc -l <filename>``, so python
        doesn't need to load the complete file twice.
    limit : int, optional
        If not `None` (default), stops the parsing once `limit` clusters have
        been read. Useful for testing purposes.

    """

    #: Size (in lines) of the header in the MemeTracker file to be parsed.
    header_size = 6

    def __init__(self, filename, line_count, limit=None):
        """Setup parsing and tracking attributes."""

        self.filename = filename
        self.line_count = line_count
        self.limit = limit

        # Keep track of if we've already parsed or not.
        self.parsed = False

        # Keep track of current cluster and quote.
        self._cluster = None
        self._quote = None

    def parse(self):
        """Parse the whole MemeTracker file, save, optimise the database, and
        check for consistency.

        Parse the MemeTracker file with :meth:`_parse` to create
        :class:`~.db.Cluster` and :class:`~.db.Quote` database entries
        corresponding to the dataset. The parsed data is then persisted to
        database in one step (with :func:`~.db.save_by_copy`). The database is
        then VACUUMed and ANALYZEd (with :func:`~.utils.execute_raw`) to force
        it to recompute its optimisations. Finally, the consistency of the
        database is checked (with :meth:`_check`) against number of quotes and
        frequency in each cluster of the original file, and against number of
        urls and frequency in each quote of the original file. Progress is
        printed to stdout.

        Note that if `self.limit` is not `None`, parsing will stop after
        `self.limit` clusters have been read.

        Once the parsing is finished, `self.parsed` is set to `True`.

        Raises
        ------
        ValueError
            If this instance has already run a parsing.

        """

        logger.info('Parsing memetracker file')
        if self.limit is not None:
            logger.info('Parsing is limited to %s clusters', self.limit)

        click.echo('Parsing MemeTracker data file into database{}...'
                   .format('' if self.limit is None
                           else ' (limit={})'.format(self.limit)))

        if self.parsed:
            raise ValueError('Parser has already run')

        # +100 is some margin for ProgressBar, otherwise it raises an exception
        # at the *end* of parsing (once the internal count exceeds max_value).
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
        """Do the actual MemeTracker file parsing.

        Initialises the parsing tracking variables, then delegates each new
        cluster block to :meth:`_parse_cluster_block`. Parsed clusters and
        quotes are stored as :class:`~.db.Cluster`\ s and
        :class:`~.db.Quote`\ s in `self._objects` (to be saved later in
        :meth:`parse`). Frequency and url counts for clusters and quotes are
        saved in `self._checks` for later checking in :meth:`parse`.

        """

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
        """Check the consistency of the database with `self._checks`.

        The original MemeTracker dataset specifies the number of quotes and
        frequency for each cluster, and the number of urls and frequency for
        each quote. This information is saved in `self._checks` during parsing.
        This method iterates through the whole database of saved
        :class:`~.db.Cluster`\ s and :class:`~.db.Quote`\ s to check that their
        counts correspond to what the MemeTracker dataset says (as stored in
        `self._checks`).

        Raises
        ------
        ValueError
            If any count in the database differs from its specification in
            `self._checks`.

        """

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
        """Parse a block of lines representing a cluster in the source
        MemeTracker file.

        The :class:`~.db.Cluster` itself is first created from
        `self._cluster_line` with :meth:`_handle_cluster`, then each following
        line is delegated to :meth:`_handle_quote` or :meth:`_handle_url` until
        exhaustion of this cluster block. During the parsing of this cluster,
        `self._cluster` holds the current cluster being filled and
        `self._quote` the current quote (both are cleaned up when the method
        finishes). At the end of this block, the method increments
        `self._clusters_read` and sets `self._cluster_line` to the line
        defining the next cluster, or `None` if the end of file or `self.limit`
        was reached.

        Raises
        ------
        ValueError
            If `self._cluster_line` is not a line defining a new cluster.

        """

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
        """Parse `line` to determine if it's a cluster-, quote- or url-line, or
        anything else.

        Parameters
        ----------
        line : str
            A line from the MemeTracker dataset to parse.

        Returns
        -------
        tipe : str in {'cluster', 'quote', 'url'} or None
            The type of object that `line` defines; `None` if unknown or empty
            line.
        fields : list of str
            List of the tab-separated fields in `line`.

        """

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
        """Handle a list of cluster fields to create a new :class:`~.db.Cluster`.

        The newly created :class:`~.db.Cluster` is appended to
        `self._objects['clusters']`, and corresponding fields are created in
        `self._checks`.

        Parameters
        ----------
        fields : list of str
            List of fields defining the new cluster, as returned by
            :meth:`_parse_line`.

        """

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
        """Handle a list of quote fields to create a new :class:`~.db.Quote`.

        The newly created :class:`~.db.Quote` is appended to
        `self._objects['quotes']`, and corresponding fields are created in
        `self._checks`.

        Parameters
        ----------
        fields : list of str
            List of fields defining the new quote, as returned by
            :meth:`_parse_line`.

        """

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
        """Handle a list of url fields to create a new :class:`~.db.Url`.

        The newly created :class:`~.db.Url` is stored on `self._quote` which
        holds the currently parsed quote.

        Parameters
        ----------
        fields : list of str
            List of fields defining the new url, as returned by
            :meth:`_parse_line`.

        """

        timestamp = datetime.strptime(fields[2], '%Y-%m-%d %H:%M:%S')
        assert timestamp.tzinfo is None

        url = Url(timestamp=timestamp, frequency=int(fields[3]),
                  url_type=fields[4], url=fields[5])
        self._quote.add_url(url)
