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

    def __init__(self, filename, line_count, limit=None):
        """Setup progress printing."""

        self.filename = filename
        self.line_count = line_count
        self.limit = limit

        # Keep track of if we've already parsed or not.
        self.parsed = False

        # Keep track of current cluster and quote.
        self.cluster = None
        self.cluster_size = None
        self.cluster_frequency = None
        self.quote = None
        self.quote_size = None
        self.quote_frequency = None

    def skip_header(self, f):
        """Skip the header lines in an open file."""

        for i in range(self.header_size):
            f.readline()

    def parse(self):
        """Parse using the defined cluster-, quote-, and url-handlers."""

        click.echo('Parsing MemeTracker data file into database{}... '
                   .format('' if self.limit is None else ' (test run)'))

        if self.parsed:
            raise ValueError('Parser has already run')

        lines_left = self.line_count - self.header_size
        with open(self.filename, 'rb', encoding='utf-8') as infile, \
                ProgressBar(max_value=lines_left, redirect_stdout=True) as bar:

            # The first lines are not data.
            self.skip_header(infile)

            cluster_line = infile.readline()
            clusters_read = 1
            lines_read = 1
            bar.update(lines_read)

            while cluster_line is not None:

                with session_scope() as session:

                    # Start this cluster
                    line0, fields = self.parse_line(cluster_line)
                    if line0[0] == '':
                        raise ValueError(
                                ("Our supposed cluster_line ('{}', line {}) "
                                 "is not a cluster line!")
                                .format(cluster_line,
                                        lines_read + self.header_size))
                    self.handle_cluster(fields)
                    session.add(self.cluster)
                    cluster_line = None

                    # And keep reading until the next one, or exhaustion
                    for line in infile:
                        lines_read += 1
                        bar.update(lines_read)

                        line0, fields = self.parse_line(line)
                        if line0[0] != '':
                            # This is a cluster definition line.

                            # Stop if asked to
                            if (self.limit is not None and
                                    clusters_read >= self.limit):
                                break

                            # Check the cluster and quote we just finished
                            if self.cluster is not None:
                                self.check_cluster()
                            # TODO: comment to see failure
                            if self.quote is not None:
                                self.check_quote()

                            # And move to next one
                            self.cluster = None
                            self.quote = None
                            cluster_line = line
                            clusters_read += 1
                            break
                        elif line[0] == '\t' and line[1] != '\t':
                            # This is a quote definition line.
                            # Check the quote we just finished
                            if self.quote is not None:
                                self.check_quote()
                            # And move to next one
                            self.handle_quote(fields)
                        elif (line[0] == '\t' and line[1] == '\t' and
                                line[2] != '\t'):
                            # This is a url definition line.
                            self.handle_url(fields)

        # Check final cluster and quote
        with session_scope() as session:
            self.cluster = session.merge(self.cluster)
            self.check_cluster()
            self.quote = session.merge(self.quote)
            self.check_quote()

        # Don't do this twice.
        self.parsed = True
        click.secho('OK', fg='green', bold=True)

    def parse_line(self, line):
        line0 = re.split(r'[\xa0\s+\t\r\n]+', line)
        return line0, re.split(r'[\t\r\n]', line)

    def check_cluster(self):
        err_end = (' #{} does not match value'
                   ' in file').format(self.cluster.sid)
        if self.cluster_size != self.cluster.size:
            raise ValueError("Cluster size" + err_end)
        if self.cluster_frequency != self.cluster.frequency:
            raise ValueError("Cluster frequency" + err_end)

    def handle_cluster(self, line_fields):
        self.cluster = Cluster(sid=int(line_fields[3]), source='memetracker')
        self.cluster_size = int(line_fields[0])
        self.cluster_frequency = int(line_fields[1])

    def check_quote(self):
        err_end = ' #{} does not match value in file'.format(self.quote.sid)
        if self.quote_size != self.quote.size:
            raise ValueError("Quote size" + err_end)
        if self.quote_frequency != self.quote.frequency:
            raise ValueError("Quote frequency" + err_end)

    def handle_quote(self, line_fields):
        self.quote = Quote(sid=int(line_fields[4]), string=line_fields[3])
        self.quote_size = int(line_fields[2])
        self.quote_frequency = int(line_fields[1])
        self.cluster.quotes.append(self.quote)

    def handle_url(self, line_fields):
        timestamp = datetime.strptime(line_fields[2], '%Y-%m-%d %H:%M:%S')
        assert timestamp.tzinfo is None

        url = Url(timestamp=timestamp, frequency=int(line_fields[3]),
                  url_type=line_fields[4], url=line_fields[5])
        self.quote.urls.append(url)
