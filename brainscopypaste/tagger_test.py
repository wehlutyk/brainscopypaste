from brainscopypaste.tagger import tag, tags, tokens, lemmas


sentence = ("Don't! I wouldn't. I've been there. The cat "
            "jumped over the fox and ate the rat")


def test_tag():
    assert tag(sentence) == (['Do', 'VV', 'do'],
                             ["n't", 'RB', "n't"],
                             ['!', 'SENT', '!'],
                             ['I', 'PP', 'I'],
                             ['would', 'MD', 'would'],
                             ["n't", 'RB', "n't"],
                             ['.', 'SENT', '.'],
                             ['I', 'PP', 'I'],
                             ["'ve", 'VHP', 'have'],
                             ['been', 'VBN', 'be'],
                             ['there', 'RB', 'there'],
                             ['.', 'SENT', '.'],
                             ['The', 'DT', 'the'],
                             ['cat', 'NN', 'cat'],
                             ['jumped', 'VVD', 'jump'],
                             ['over', 'IN', 'over'],
                             ['the', 'DT', 'the'],
                             ['fox', 'NN', 'fox'],
                             ['and', 'CC', 'and'],
                             ['ate', 'VVD', 'eat'],
                             ['the', 'DT', 'the'],
                             ['rat', 'NN', 'rat'])


def test_tags():
    assert tags(sentence) == ('VV', 'RB', 'SENT', 'PP', 'MD', 'RB', 'SENT',
                              'PP', 'VHP', 'VBN', 'RB', 'SENT', 'DT', 'NN',
                              'VVD', 'IN', 'DT', 'NN', 'CC', 'VVD', 'DT', 'NN')


def test_tokens():
    assert tokens(sentence) == ('Do', "n't", '!', 'I', 'would', "n't", '.',
                                'I', "'ve", 'been', 'there', '.', 'The', 'cat',
                                'jumped', 'over', 'the', 'fox', 'and', 'ate',
                                'the', 'rat')


def test_lemmas():
    assert lemmas(sentence) == ('do', "n't", '!', 'I', 'would', "n't", '.',
                                'I', 'have', 'be', 'there', '.', 'the', 'cat',
                                'jump', 'over', 'the', 'fox', 'and', 'eat',
                                'the', 'rat')
