import click
from progressbar import ProgressBar

from brainscopypaste.utils import (is_int, is_same_ending_us_uk_spelling,
                                   levenshtein, stopwords, session_scope)


def mine_substitutions(model, limit=None):
    # TODO: test
    from brainscopypaste.db import Cluster

    click.echo('Mining clusters for substitutions{}...'
               .format('' if limit is None else ' (test run)'))

    with session_scope() as session:
        if session.query(Cluster)\
           .filter(Cluster.filtered.is_(True)).count() == 0:
            raise Exception('Found no filtered clusters, aborting.')

        query = session.query(Cluster.id).filter(Cluster.filtered.is_(True))
        if limit is not None:
            query = query.limit(limit)
        cluster_ids = [id for (id,) in query]

    seen = 0
    kept = 0
    for cluster_id in ProgressBar()(cluster_ids):
        with session_scope() as session:
            cluster = session.query(Cluster).get(cluster_id)
            for substitution in cluster.substitutions(model):
                seen += 1
                if substitution.validate():
                    kept += 1
                    session.add(substitution)

    click.secho('OK', fg='green', bold=True)
    click.echo('Seen {} candidate substitutions, kept {}.'.format(seen, kept))


class Model:
    # time: continuous/discrete
    # source: all/majority
    # past: all/last bin
    # destination: all/not in past
    pass


class SourceValidator:
    pass


class DestinationValidator:
    pass


class MinerMixin:

    def substitutions(self, model):
        # TODO: test
        # iterate over all candidate substitutions in the cluster
        pass


class ValidatorMixin:

    def validate(self):
        # TODO: test

        word1, word2 = self.words
        lem1, lem2 = self.lemmas

        # '21st'/'twenty-first', etc.
        if (is_int(word1[0]) or is_int(word2[0]) or
                is_int(lem1[0]) or is_int(lem2[0])):
            return False
        # 'sen'/'senator', 'gov'/'governor', 'nov'/'november', etc.
        if (word1 == word2[:3] or word2 == word1[:3] or
                lem1 == lem2[:3] or lem2 == lem1[:3]):
            return False
        # 'programme'/'program', etc.
        if (word1[:-2] == word2 or word2[:-2] == word1 or
                lem1[:-2] == lem2 or lem2[:-2] == lem1):
            return False
        # 'centre'/'center', etc.
        if is_same_ending_us_uk_spelling(word1, word2):
            return False
        if is_same_ending_us_uk_spelling(lem1, lem2):
            return False
        # stopwords
        if (word1 in stopwords or word2 in stopwords or
                lem1 in stopwords or lem2 in stopwords):
            return False
        # Other minor spelling changes
        if levenshtein(word1, word2) <= 1:
            return False
        if levenshtein(lem1, lem2) <= 1:
            return False

        return True
