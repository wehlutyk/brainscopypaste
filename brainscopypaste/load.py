"""Load data from the MemeTracker dataset."""


from datetime import datetime
import re
from codecs import open
from io import StringIO

import click
from progressbar import ProgressBar

from brainscopypaste.db import Session, Cluster, Quote, Url
from brainscopypaste.utils import session_scope


class MemeTrackerParser:

    """Parse the MemeTracker file into database."""

    # How many lines to skip at the beginning of the file.
    header_size = 6

    # We save to database and check every `block_size` clusters.
    block_size = None

    # Format strings to create file lines from cluster, quote, url.
    cluster_format = ('{cluster.id}\t{cluster.sid}\t{cluster.filtered}'
                      '\t{cluster.source}\n')
    cluster_columns = ('id', 'sid', 'filtered', 'source')
    quote_format = ('{quote.id}\t{quote.cluster_id}\t{quote.sid}'
                    '\t{quote.filtered}\t{quote.string}\n')
    quote_columns = ('id', 'cluster_id', 'sid', 'filtered', 'string')
    url_format = ('{url.quote_id}\t{url.filtered}\t{url.timestamp}'
                  '\t{url.frequency}\t{url.url_type}\t{url.url}\n')
    url_columns = ('quote_id', 'filtered', 'timestamp', 'frequency',
                   'url_type', 'url')

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

        click.echo('Parsing MemeTracker data file into db-copyable file{}... '
                   .format('' if self.limit is None else ' (test run)'))

        if self.parsed:
            raise ValueError('Parser has already run')

        # +100 is some margin for ProgressBar
        lines_left = self.line_count - self.header_size + 100
        with open(self.filename, 'rb', encoding='utf8') as self._file, \
                ProgressBar(max_value=lines_left,
                            redirect_stdout=True) as self._bar:
            self._parse()

        # Don't do this twice.
        self.parsed = True
        click.secho('OK', fg='green', bold=True)

        # Vacuum analyze
        click.echo('Vacuuming and analyzing anew... ', nl=False)
        connection = Session.kw['bind'].connect()
        raw_connection = connection.connection
        old_isolation_level = raw_connection.isolation_level
        raw_connection.set_isolation_level(0)
        with raw_connection.cursor() as cursor:
            cursor.execute('VACUUM ANALYZE')
        raw_connection.set_isolation_level(old_isolation_level)
        connection.close()
        click.secho('OK', fg='green', bold=True)

    def _parse(self):

        # The first lines are not data.
        self._skip_header()

        # Initialize the parsing with the first line.
        self._cluster_line = self._file.readline()
        self._clusters_read = 0
        self._lines_read = 1
        self._bar.update(self._lines_read)

        # Results to be saved periodically.
        self._objects = {'clusters': [], 'quotes': [], 'urls': []}
        self._checks = {'clusters': {}, 'quotes': {}}

        while self._cluster_line is not None:
            self._parse_cluster_block()
            if (self.block_size is not None and
                    self._clusters_read % self.block_size == 0):
                self._save()
                self._check()

        # Final save and check.
        self._save()
        self._check()

    def _save(self):
        # Order the objects inserted so the engine bulks them together.
        objects = StringIO()
        objects.writelines(self._objects['clusters'])
        self._copy(objects, Cluster.__tablename__, self.cluster_columns)
        objects.close()

        objects = StringIO()
        objects.writelines(self._objects['quotes'])
        self._copy(objects, Quote.__tablename__, self.quote_columns)
        objects.close()

        objects = StringIO()
        objects.writelines(self._objects['urls'])
        self._copy(objects, Url.__tablename__, self.url_columns)
        objects.close()

        self._objects = {'clusters': [], 'quotes': [], 'urls': []}

    def _copy(self, string, table, columns):
        string.seek(0)
        with session_scope() as session:
            cursor = session.connection().connection.cursor()
            cursor.copy_from(string, table, columns=columns)

    def _check(self):
        with session_scope() as session:
            for id, check in self._checks['clusters'].items():
                # Check the cluster itself.
                cluster = session.query(Cluster).get(id)
                err_end = (' #{} does not match value'
                           ' in file').format(cluster.sid)
                if check['size'] != cluster.size:
                    raise ValueError("Cluster size" + err_end)
                if check['frequency'] != cluster.frequency:
                    raise ValueError("Cluster frequency" + err_end)

                # Check each quote.
                for quote in cluster.quotes:
                    check = self._checks['quotes'][quote.id]
                    err_end = (' #{} does not match value'
                               ' in file').format(quote.sid)
                    if check['size'] != quote.size:
                        raise ValueError("Quote size" + err_end)
                    if check['frequency'] != quote.frequency:
                        raise ValueError("Quote frequency" + err_end)

        self._checks = {'clusters': {}, 'quotes': {}}

    def _parse_cluster_block(self):
        # Check we have a cluster line and parse it.
        tipe, fields = self._parse_line(self._cluster_line)
        # If self._cluster_line stays None, _parse() stops.
        # So it's filled further down when we get to the next cluster
        # definition line (unless self.limit says we should read
        # only a subset of all clusters).
        self._cluster_line = None
        if tipe != 'cluster':
            raise ValueError(
                ("Our supposed cluster_line ('{}', line {}) "
                 "is not a cluster line!").format(
                     self._cluster_line, self._lines_read + self.header_size))

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
        self._objects['clusters'].append(
            self.cluster_format.format(cluster=self._cluster))

        # Save checks for later on.
        cluster_size = int(fields[0])
        cluster_frequency = int(fields[1])
        self._checks['clusters'][self._cluster.id] = {
            'size': cluster_size,
            'frequency': cluster_frequency
        }

    def _handle_quote(self, fields):
        id = int(fields[4])
        # Backslashes must be escaped otherwise PostgreSQL interprets them
        # in its own way (see
        # http://www.postgresql.org/docs/current/interactive/sql-copy.html).
        self._quote = Quote(cluster_id=self._cluster.id,
                            id=id, sid=id,
                            filtered=False,
                            string=fields[3].replace('\\', '\\\\'))
        self._objects['quotes'].append(
            self.quote_format.format(quote=self._quote))

        # Save checks for later on.
        quote_size = int(fields[2])
        quote_frequency = int(fields[1])
        self._checks['quotes'][self._quote.id] = {
            'size': quote_size,
            'frequency': quote_frequency
        }

    def _handle_url(self, fields):
        timestamp = datetime.strptime(fields[2], '%Y-%m-%d %H:%M:%S')
        assert timestamp.tzinfo is None

        # Backslashes must be escaped otherwise PostgreSQL interprets them
        # in its own way (see
        # http://www.postgresql.org/docs/current/interactive/sql-copy.html).
        url = Url(quote_id=self._quote.id,
                  filtered=False,
                  timestamp=timestamp, frequency=int(fields[3]),
                  url_type=fields[4], url=fields[5].replace('\\', '\\\\'))
        self._objects['urls'].append(
            self.url_format.format(url=url))
