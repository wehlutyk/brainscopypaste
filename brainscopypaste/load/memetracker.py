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

    # Number of lines of the file
    n_lines = 8357595

    def __init__(self, filename, limitlines=None, nochecks=False):
        """Setup progress printing."""

        self.filename = filename
        self.limitlines = limitlines
        self.nochecks = nochecks

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

        n_lines = (self.n_lines if self.limitlines is None
                   else self.limitlines) - self.header_size + 1
        click.echo('Parsing MemeTracker data file into database{}... '
                   .format('' if self.limitlines is None else ' (test run)'))
        bar = ProgressBar(max_value=n_lines, redirect_stdout=True)

        if self.parsed:
            raise ValueError('Parser has already run')

        with open(self.filename, 'rb', encoding='utf-8') as infile:

            # The first lines are not data.
            self.skip_header(infile)

            # Parse the file.
            with session_scope() as session:
                self.session = session

                for i, line in enumerate(infile):
                    bar.update(i)
                    if self.limitlines is not None and i >= n_lines:
                        break

                    line0 = re.split(r'[\xa0\s+\t\r\n]+', line)
                    line_fields = re.split(r'[\t\r\n]', line)

                    if line0[0] != '':
                        # This is a cluster definition line.
                        self.handle_cluster(line_fields)
                    elif line[0] == '\t' and line[1] != '\t':
                        # This is a quote definition line.
                        self.handle_quote(line_fields)
                    elif (line[0] == '\t' and line[1] == '\t' and
                            line[2] != '\t'):
                        # This is a url definition line.
                        self.handle_url(line_fields)

                # Check final cluster and quote
                self.check_cluster()
                self.check_quote()

        # Don't do this twice.
        self.parsed = True
        bar.finish()
        click.secho('OK', fg='green', bold=True)

    def check_cluster(self):
        err_end = (' #{} does not match value'
                   ' in file').format(self.cluster.id)
        if not self.nochecks and self.cluster_size != self.cluster.size:
            raise ValueError("Cluster size" + err_end)
        if (not self.nochecks and
                self.cluster_frequency != self.cluster.frequency):
            raise ValueError("Cluster frequency" + err_end)

    def handle_cluster(self, line_fields):
        if self.cluster is not None:
            self.check_cluster()
            self.session.commit()

        self.cluster = Cluster(id=int(line_fields[3]), source='memetracker')
        self.cluster_size = int(line_fields[0])
        self.cluster_frequency = int(line_fields[1])
        self.session.add(self.cluster)

    def check_quote(self):
        err_end = ' #{} does not match value in file'.format(self.quote.id)
        if not self.nochecks and self.quote_size != self.quote.size:
            raise ValueError("Quote size" + err_end)
        if not self.nochecks and self.quote_frequency != self.quote.frequency:
            raise ValueError("Quote frequency" + err_end)

    def handle_quote(self, line_fields):
        if self.quote is not None:
            self.check_quote()
            self.session.commit()

        self.quote = Quote(id=int(line_fields[4]), string=line_fields[3])
        self.quote_size = int(line_fields[2])
        self.quote_frequency = int(line_fields[1])
        self.cluster.quotes.append(self.quote)

    def handle_url(self, line_fields):
        timestamp = datetime.strptime(line_fields[2], '%Y-%m-%d %H:%M:%S')
        assert timestamp.tzinfo is None

        url = Url(timestamp=timestamp, frequency=int(line_fields[3]),
                  url_type=line_fields[4], url=line_fields[5])
        self.quote.urls.append(url)
