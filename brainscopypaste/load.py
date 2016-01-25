"""Load data from the MemeTracker dataset."""


from datetime import datetime
import re
from codecs import open

import click
from progressbar import ProgressBar

from brainscopypaste.db import Cluster, Quote, Url
from brainscopypaste.utils import session_scope


class MemeTrackerParser:

    """Parse the MemeTracker file into database."""

    # How many lines to skip at the beginning of the file.
    header_size = 6

    # We save to database and check every `block_size` clusters.
    block_size = 100

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

        click.echo('Parsing MemeTracker data file into database{}... '
                   .format('' if self.limit is None else ' (test run)'))

        if self.parsed:
            raise ValueError('Parser has already run')

        lines_left = self.line_count - self.header_size
        with open(self.filename, 'rb', encoding='utf-8') as self._file, \
                ProgressBar(max_value=lines_left,
                            redirect_stdout=True) as self._bar:
            self._parse()

        # Don't do this twice.
        self.parsed = True
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
            if self._clusters_read % self.block_size == 0:
                self._save()
                self._check()

        # Final save and check.
        self._save()
        self._check()

    def _save(self):
        with session_scope() as session:
            # Order the objects inserted so the engine bulks them together.
            objects = []
            objects.extend(self._objects['clusters'])
            objects.extend(self._objects['quotes'])
            objects.extend(self._objects['urls'])
            session.bulk_save_objects(objects)

        self._objects = {'clusters': [], 'quotes': [], 'urls': []}

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
        self._cluster = Cluster(id=id, sid=id, source='memetracker')
        self._objects['clusters'].append(self._cluster)

        # Save checks for later on.
        cluster_size = int(fields[0])
        cluster_frequency = int(fields[1])
        self._checks['clusters'][self._cluster.id] = {
            'size': cluster_size,
            'frequency': cluster_frequency
        }

    def _handle_quote(self, fields):
        id = int(fields[4])
        self._quote = Quote(cluster_id=self._cluster.id,
                            id=id, sid=id, string=fields[3])
        self._objects['quotes'].append(self._quote)

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

        url = Url(quote_id=self._quote.id,
                  timestamp=timestamp, frequency=int(fields[3]),
                  url_type=fields[4], url=fields[5])
        self._objects['urls'].append(url)
