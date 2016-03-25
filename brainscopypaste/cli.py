import logging

import click
from sqlalchemy import create_engine

from brainscopypaste.db import Base, Session, Cluster, Substitution
from brainscopypaste.utils import session_scope
from brainscopypaste.load import (MemeTrackerParser, load_fa_features,
                                  load_mt_frequency)
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


def init_db(echo_sql):
    logger.info('Initializing database connection')

    engine = create_engine('postgresql+psycopg2://brainscopypaste:'
                           '@localhost:5432/brainscopypaste',
                           client_encoding='utf8', echo=echo_sql)
    Session.configure(bind=engine)

    logger.info('Database connected')
    logger.debug('Checking tables to create')

    Base.metadata.create_all(engine)
    return engine


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
    """Empty the whole database."""

    if confirm('the whole database'):
        logger.info('Emptying database')

        click.secho('Emptying database... ', nl=False)
        Base.metadata.drop_all(bind=obj['engine'])
        click.secho('OK', fg='green', bold=True)

        logger.info('Done emptying database')


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
    load_mt_frequency()
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
    logger.info('Done mining substitution in memetracker data')


def cliobj():
    cli(obj={})


if __name__ == '__main__':
    cliobj()
