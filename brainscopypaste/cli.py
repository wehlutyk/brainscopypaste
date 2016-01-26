import click
from sqlalchemy import create_engine

from brainscopypaste import paths
from brainscopypaste.db import Base, Session, Cluster, Quote, Url
from brainscopypaste.utils import session_scope
from brainscopypaste.load import MemeTrackerParser
from brainscopypaste.filter import filter_clusters


@click.group()
@click.option('--echo-sql', is_flag=True)
@click.pass_obj
def cli(obj, echo_sql):
    """BrainsCopyPaste analysis of the MemeTracker data."""
    obj['ECHO_SQL'] = echo_sql


def init_db(echo_sql):
    click.echo('Initializing database connection... ', nl=False)
    engine = create_engine('postgresql://brainscopypaste:'
                           '@localhost:5432/brainscopypaste',
                           echo=echo_sql)
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)
    click.secho('OK', fg='green', bold=True)
    return engine


@cli.group()
@click.pass_obj
def drop(obj):
    """Drop parts of (or all) the database."""
    obj['engine'] = init_db(obj['ECHO_SQL'])


def confirm(fillin):
    text = "About to empty {}. Are you sure? (type 'yes') ".format(fillin)
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
        click.secho('Emptying database... ', nl=False)
        Base.metadata.drop_all(bind=obj['engine'])
        click.secho('OK', fg='green', bold=True)


@drop.command(name='filtered')
@click.pass_obj
def drop_filtered(obj):
    """Drop filtered models (Clusters, Quotes, Urls)."""
    if confirm('the filtered models (Clusters, Quotes, Urls)'):
        with session_scope() as session:
            click.secho('Dropping filtered models... ', nl=False)
            session.query(Cluster).filter(Cluster.filtered.is_(True)).delete()
            session.query(Quote).filter(Quote.filtered.is_(True)).delete()
            session.query(Url).filter(Url.filtered.is_(True)).delete()
        click.secho('OK', fg='green', bold=True)


@cli.group()
@click.pass_obj
def load(obj):
    """Source database loading."""
    init_db(obj['ECHO_SQL'])


@load.command(name='memetracker')
@click.option('--testrun', is_flag=True)
def load_memetracker(testrun):
    """Load MemeTracker data into SQL."""
    MemeTrackerParser(paths.mt_full,
                      line_count=8357595,
                      limit=3 if testrun else None)\
        .parse()


@cli.group()
@click.pass_obj
def filter(obj):
    """Source database filtering."""
    init_db(obj['ECHO_SQL'])


@filter.command(name='memetracker')
@click.option('--testrun', is_flag=True)
def filter_memetracker(testrun):
    """Filter MemeTracker data."""
    filter_clusters(limit=3 if testrun else None)


def cliobj():
    cli(obj={})


if __name__ == '__main__':
    cliobj()
