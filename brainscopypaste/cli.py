import click
from sqlalchemy import create_engine

from brainscopypaste import paths
from brainscopypaste.db import Base, Session
from brainscopypaste.load.memetracker import MemeTrackerParser


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


@cli.command()
def emptydb():
    """Empty the database."""
    engine = init_db()
    click.secho("About to empty the whole database. "
                "Are you sure? (type 'yes') ", nl=False,
                fg='red', bold=True)
    answer = input()

    if answer != 'yes':
        click.secho("Good. Aborting.")
        return

    click.secho('Emptying database... ', nl=False)
    Base.metadata.drop_all(bind=engine)
    click.secho('OK', fg='green', bold=True)


@cli.group()
def load():
    """Source database loading."""
    init_db()


@load.command()
@click.option('--testrun', is_flag=True)
def memetracker(testrun):
    """Load MemeTracker data into SQL."""
    MemeTrackerParser().parse(paths.mt_full, testrun=testrun)


if __name__ == '__main__':
    cli(obj={})
