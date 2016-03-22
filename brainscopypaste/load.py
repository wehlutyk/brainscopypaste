"""Load data from the MemeTracker dataset."""


from datetime import datetime
import re
from codecs import open
import logging

import click
from progressbar import ProgressBar

from brainscopypaste.db import Session, Cluster, Quote, Url, save_by_copy
from brainscopypaste.utils import session_scope, execute_raw


logger = logging.getLogger(__name__)


# TODO: FA norms loader and feature computation (maybe in utils)
# TODO: Frequency loader and feature computation


class MemeTrackerParser:

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

    def _skip_header(self):
        """Skip the header lines in the open file."""

        for i in range(self.header_size):
            self._file.readline()

    def parse(self):
        """Parse using the defined cluster-, quote-, and url-handlers."""

        logger.info('Parsing memetracker file')
        if self.limit is not None:
            logger.info('Parsing is limited to %s clusters', self.limit)

        click.echo('Parsing MemeTracker data file into database{}... '
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
