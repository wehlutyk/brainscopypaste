import click
from sqlalchemy import create_engine

from db import Base, Session


@click.group()
def cli():
    """BrainsCopyPaste analysis of the MemeTracker data."""


def init_db():
    click.echo('Initializing database connection')
    engine = create_engine('postgresql://brainscopypaste:'
                           '@localhost:5432/brainscopypaste')
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)


@cli.group()
def load():
    """Source database loading."""
    init_db()


@load.command()
def memetracker():
    """Load MemeTracker data into SQL."""
    pass


if __name__ == '__main__':
    cli(obj={})
