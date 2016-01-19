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

    def __init__(self, filename):
        """Setup progress printing."""

        self.filename = filename

        # Keep track of if we've already parsed or not.
        self.parsed = False

        # Keep track of current cluster and quote.
        self.cluster = None
        self.quote = None

    def skip_header(self, f):
        """Skip the header lines in an open file."""

        for i in range(self.header_size):
            f.readline()

    def parse(self, limitlines=None):
        """Parse using the defined cluster-, quote-, and url-handlers."""

        n_lines = (self.n_lines if limitlines is None else limitlines) - \
            self.header_size + 1
        click.echo('Parsing MemeTracker data file into database{}... '
                   .format('' if limitlines is None else ' (test run)'))
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
                    if limitlines is not None and i >= n_lines:
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

        # Don't do this twice.
        self.parsed = True
        bar.finish()
        click.secho('OK', fg='green', bold=True)

    def handle_cluster(self, line_fields):
        if self.cluster is not None:
            self.session.commit()
        self.cluster = Cluster(id=int(line_fields[3]), source='memetracker')
        self.session.add(self.cluster)

    def handle_quote(self, line_fields):
        self.quote = Quote(id=int(line_fields[4]), string=line_fields[3])
        self.cluster.quotes.append(self.quote)

    def handle_url(self, line_fields):
        timestamp = datetime.strptime(line_fields[2], '%Y-%m-%d %H:%M:%S')
        assert timestamp.tzinfo is None

        url = Url(timestamp=timestamp, frequency=int(line_fields[3]),
                  url_type=line_fields[4], url=line_fields[5])
        self.quote.urls.append(url)
