from linguistics.treetagger import TaggerBuilder


def build_n_quotes_to_clusterids(clusters):
    """Build a dictionary associating number of Quotes to Cluster ids having
    that number of quotes.

    Arguments:
      * The RedisDataAccess Clusters connection or dict of Clusters to work on

    Returns: the dict of 'number of Quotes' -> 'sequence of Cluster ids'.

    """

    inv_cl_lengths = {}

    for cl_id, cl in clusters.iteritems():

        if inv_cl_lengths.has_key(cl.n_quotes):
            inv_cl_lengths[cl.n_quotes].append(cl_id)
        else:
            inv_cl_lengths[cl.n_quotes] = [cl_id]

    return inv_cl_lengths


def build_quotelengths_to_n_quote(clusters):
    """Build a dict associating Quote string lengths to the number of Quotes
    having that string length.

    Arguments:
      * The RedisDataAccess Clusters connection or dict of Clusters to work on

    Returns: the dict of 'Quote string lengths' -> 'number of Quotes having
             that string length'.

    """

    tagger = TaggerBuilder.get_tagger()

    inv_qt_lengths = {}

    for cl in clusters.itervalues():

        for qt in cl.quotes.itervalues():

            n_words = len(tagger.Tokenize(qt.string.lower()))

            if inv_qt_lengths.has_key(n_words):
                inv_qt_lengths[n_words] += 1
            else:
                inv_qt_lengths[n_words] = 1

    return inv_qt_lengths


