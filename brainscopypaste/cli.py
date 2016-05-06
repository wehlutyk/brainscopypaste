from os.path import exists, basename, split, join
from os import remove
import logging
import re

import click
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

from brainscopypaste.db import Base, Cluster, Substitution
from brainscopypaste.utils import session_scope, init_db
from brainscopypaste.load import (MemeTrackerParser, load_fa_features,
                                  load_mt_frequency_and_tokens)
from brainscopypaste.filter import filter_clusters
from brainscopypaste.mine import (mine_substitutions_with_model, Time, Source,
                                  Past, Durl, Model)
from brainscopypaste.conf import settings


logger = logging.getLogger(__name__)


@click.group()
@click.option('--echo-sql', is_flag=True)
@click.option('--log', default='info', type=click.Choice(['info', 'debug']),
              help='Set log level')
@click.option('--log-file', default=None, type=click.Path(),
              help='Log to this file instead of stdout')
@click.pass_obj
def cli(obj, echo_sql, log, log_file):
    """BrainsCopyPaste analysis of the MemeTracker data."""

    # Configure logging and silence TreeTagger logs.
    loglevel = getattr(logging, log.upper())
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s: '
                        '%(message)s', level=loglevel, filename=log_file)
    logging.getLogger('TreeTagger').setLevel(logging.WARNING)
    logger.debug('Logging configured')

    # Save config.
    obj['ECHO_SQL'] = echo_sql
    obj['engine'] = init_db(obj['ECHO_SQL'])


@cli.group()
def drop():
    """Drop parts of (or all) the database."""


def confirm(fillin):
    text = "About to drop {}. Are you sure? (type 'yes') ".format(fillin)
    click.secho(text, nl=False, fg='red', bold=True)
    answer = input()

    if answer == 'yes':
        return True
    else:
        click.secho("Good. Aborting.")
        return False


@drop.command(name='all')
@click.pass_obj
def drop_all(obj):
    """Empty the whole database and all features."""

    if confirm('the whole database and all features'):
        logger.info('Emptying database')
        click.secho('Emptying database... ', nl=False)

        Base.metadata.drop_all(bind=obj['engine'])

        click.secho('OK', fg='green', bold=True)
        logger.info('Done emptying database')

        _drop_features()


@drop.command(name='filtered')
@click.pass_obj
def drop_filtered(obj):
    """Drop filtered rows (Clusters, Quotes)."""

    click.secho('Dropping filtered rows will also drop any substitutions '
                'mined beforehand', bold=True)

    if confirm('the filtered rows (clusters, quotes) and '
               'any mined substitutions attached to them'):
        logger.info('Dropping filtered rows (quotes and clusters) and '
                    'substitutions from database')

        with session_scope() as session:
            click.secho('Dropping filtered rows and substitutions... ',
                        nl=False)
            session.query(Cluster).filter(Cluster.filtered.is_(True))\
                   .delete(synchronize_session=False)

        click.secho('OK', fg='green', bold=True)
        logger.info('Done dropping filtered rows and substitutions')


@drop.command(name='substitutions')
@click.pass_obj
def drop_substitutions(obj):
    """Drop Substitutions."""

    if confirm('the mined substitutions'):
        logger.info('Dropping substitutions from database')
        click.secho('Dropping mined substitutions... ', nl=False)

        Substitution.__table__.drop(bind=obj['engine'])

        click.secho('OK', fg='green', bold=True)
        logger.info('Done dropping substitutions')


def _drop_features():
    logger.info('Dropping computed features from filesystem')
    click.secho('Dropping computed features... ', nl=False)

    for file in [settings.DEGREE, settings.PAGERANK, settings.BETWEENNESS,
                 settings.CLUSTERING, settings.FREQUENCY, settings.TOKENS]:
        if exists(file):
            logger.debug("Dropping '%s'", basename(file))
            remove(file)
        else:
            logger.debug("'%s' not present, no need to drop it",
                         basename(file))

    click.secho('OK', fg='green', bold=True)
    logger.info('Done dropping features')


@drop.command(name='features')
def drop_features():
    """Drop computed features."""
    if confirm('the computed features'):
        _drop_features()


@cli.group()
def load():
    """Source database loading."""


@load.command(name='memetracker')
@click.option('--limit', default=None, type=int,
              help='Limit number of clusters processed')
def load_memetracker(limit):
    """Load MemeTracker data into SQL."""

    logger.info('Starting load of memetracker data into database')
    MemeTrackerParser(settings.MT_SOURCE, line_count=settings.MT_LENGTH,
                      limit=limit).parse()
    logger.info('Done loading memetracker data into database')


@load.command(name='features')
def load_features():
    """Compute features and save them to pickle."""

    logger.info('Starting computation of features')
    load_mt_frequency_and_tokens()
    load_fa_features()
    logger.info('Done computing and saving features')


@cli.group()
def filter():
    """Source database filtering."""


@filter.command(name='memetracker')
@click.option('--limit', default=None, type=int,
              help='Limit number of clusters processed')
def filter_memetracker(limit):
    """Filter MemeTracker data."""

    logger.info('Starting filtering of memetracker data')
    filter_clusters(limit=limit)
    logger.info('Done filtering memetracker data')


@cli.group()
def mine():
    """Mine the database."""


@mine.command(name='substitutions')
@click.argument('time', type=click.Choice(map('{}'.format, Time)))
@click.argument('source', type=click.Choice(map('{}'.format, Source)))
@click.argument('past', type=click.Choice(map('{}'.format, Past)))
@click.argument('durl', type=click.Choice(map('{}'.format, Durl)))
@click.option('--limit', default=None, type=int,
              help='Limit number of clusters processed')
def mine_substitutions(time, source, past, durl, limit):
    """Mine the database for substitutions."""

    time, source, past, durl = map(lambda s: s.split('.')[1],
                                   [time, source, past, durl])
    model = Model(time=Time[time], source=Source[source],
                  past=Past[past], durl=Durl[durl])

    logger.info('Starting substitution mining in memetracker data')
    if limit is not None:
        logger.info('Substitution mining is limited to %s clusters', limit)
    logger.info('Substitution model is %s', model)

    mine_substitutions_with_model(model, limit=limit)
    logger.info('Done mining substitutions in memetracker data')


@cli.group()
def variant():
    """Generate or run variants of the analysis notebooks."""


def _notebook_variant_path(nb_file, model):
    folder, filename = split(nb_file)
    return join(settings.NOTEBOOKS_VARIANTS, '{} - {}'.format(model, filename))


@variant.command(name='generate')
@click.argument('time', type=click.Choice(map('{}'.format, Time)))
@click.argument('source', type=click.Choice(map('{}'.format, Source)))
@click.argument('past', type=click.Choice(map('{}'.format, Past)))
@click.argument('durl', type=click.Choice(map('{}'.format, Durl)))
@click.argument('notebook', type=click.Path(exists=True))
def variant_generate(time, source, past, durl, notebook):
    """Generate a variant of an analysis notebooks based on a different
    substitution model."""

    # Get model object.
    time, source, past, durl = map(lambda s: s.split('.')[1],
                                   [time, source, past, durl])
    model = Model(time=Time[time], source=Source[source],
                  past=Past[past], durl=Durl[durl])
    model_str = '{}'.format(model)

    # Read the source notebook, and generate the appropriate variant.
    logger.debug("Reading notebook '{}'".format(notebook))
    with open(notebook) as f:
        nb = nbformat.read(f, as_version=4)

    logger.info("Creating notebook '{}' variant {}".format(notebook, model))
    for cell in nb.cells:
        cell['source'] = re.sub(r'Model\(.*?\)', model_str, cell['source'])
        if 'outputs' in cell:
            cell['outputs'] = []
        if 'execution_count' in cell:
            cell['execution_count'] = None

    logger.debug("Saving notebook '{}' variant {}".format(notebook, model))
    with open(_notebook_variant_path(notebook, model), 'wt') as f:
        nbformat.write(nb, f)


@variant.command(name='run')
@click.argument('time', type=click.Choice(map('{}'.format, Time)))
@click.argument('source', type=click.Choice(map('{}'.format, Source)))
@click.argument('past', type=click.Choice(map('{}'.format, Past)))
@click.argument('durl', type=click.Choice(map('{}'.format, Durl)))
@click.argument('notebook', type=click.Path(exists=True))
def variant_run(time, source, past, durl, notebook):
    """Run a variant of an analysis notebooks based on a different
    substitution model."""

    time, source, past, durl = map(lambda s: s.split('.')[1],
                                   [time, source, past, durl])
    model = Model(time=Time[time], source=Source[source],
                  past=Past[past], durl=Durl[durl])
    notebook = _notebook_variant_path(notebook, model)

    logger.debug("Reading notebook '{}'".format(notebook))
    if not exists(notebook):
        raise Exception("Couldn't find notebook '{}'".format(notebook))
    with open(notebook) as f:
        nb = nbformat.read(f, as_version=4)

    logger.info("Executing notebook '{}'".format(notebook))
    ep = ExecutePreprocessor(timeout=12*3600, kernel_name='python3')
    ep.preprocess(nb, {'metadata': {'path': settings.NOTEBOOKS}})

    logger.debug("Saving notebook '{}'".format(notebook))
    with open(notebook, 'wt') as f:
        nbformat.write(nb, f)


def cliobj():
    cli(obj={})


if __name__ == '__main__':
    cliobj()
