import click
from sqlalchemy import create_engine

from brainscopypaste import paths
from brainscopypaste.db import Base, Session, Cluster, Quote, Url
from brainscopypaste.utils import session_scope
from brainscopypaste.load import MemeTrackerParser


@click.group()
def cli():
    """BrainsCopyPaste analysis of the MemeTracker data."""


def init_db():
    click.echo('Initializing database connection... ', nl=False)
    engine = create_engine('postgresql://brainscopypaste:'
                           '@localhost:5432/brainscopypaste')
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)
    click.secho('OK', fg='green', bold=True)
    return engine


@cli.group()
@click.pass_obj
def drop(obj):
    """Drop parts of (or all) the database."""
    obj['engine'] = init_db()


def confirm(fillin):
    text = "About to empty {}. Are you sure? (type 'yes') ".format(fillin)
    click.secho(text, nl=False, fg='red', bold=True)
    answer = input()

    if answer == 'yes':
        return True
    else:
        click.secho("Good. Aborting.")
        return False


@drop.command()
@click.pass_obj
def all(obj):
    """Empty the whole database."""
    if confirm('the whole database'):
        click.secho('Emptying database... ', nl=False)
        Base.metadata.drop_all(bind=obj['engine'])
        click.secho('OK', fg='green', bold=True)


@drop.command()
@click.pass_obj
def filtered(obj):
    """Drop filtered models (Clusters, Quotes, Urls)."""
    if confirm('the filtered models (Clusters, Quotes, Urls)'):
        with session_scope() as session:
            click.secho('Dropping filtered models... ', nl=False)
            session.query(Cluster).filter(Cluster.filtered.is_(True)).delete()
            session.query(Quote).filter(Quote.filtered.is_(True)).delete()
            session.query(Url).filter(Url.filtered.is_(True)).delete()
        click.secho('OK', fg='green', bold=True)


@cli.group()
def load():
    """Source database loading."""
    init_db()


@load.command(name='memetracker')
@click.option('--testrun', is_flag=True)
def load_memetracker(testrun):
    """Load MemeTracker data into SQL."""
    MemeTrackerParser(paths.mt_full,
                      line_count=8357595,
                      limit=3 if testrun else None)\
        .parse()


@cli.group()
def filter():
    """Source database filtering."""
    init_db()


@filter.command(name='memetracker')
def filter_memetracker(testrun):
    """Filter MemeTracker data."""
    # TODO: implement


def cliobj():
    cli(obj={})


if __name__ == '__main__':
    cliobj()
