import json
import logging

import nltk
from nltk.corpus import brown


from flask import Flask

from flask import request, make_response

import itertools, string

from settings import SERVICES

app = Flask(__name__)


def extract_candidate_chunks(text, grammar=r"KT: {(<JJ>* <NN.*>+ <IN>)? <JJ>* <NN.*>+}"):
    """
    step 1
    """

    punct = set(string.punctuation)
    print(punct)

    stop_words = set(nltk.corpus.stopwords.words("english"))
    print stop_words

    chunker = nltk.chunk.regexp.RegexpParser(grammar)
    print chunker

    tagged_sents = nltk.pos_tag_sents(nltk.word_tokenize(sent) for sent in nltk.sent_tokenize(text))
    print tagged_sents

    all_chunks = list(itertools.chain.from_iterable(nltk.chunk.tree2conlltags(chunker.parse(tagged_sent))
                                                    for tagged_sent in tagged_sents))
    candidates = [" ".join(w for w,p,c in group).lower()
                  for key, group in itertools.groupby(all_chunks, lambda (w, p, c): c != 'O') if key]

    return [c for c in candidates if c not in stop_words and not all(char in punct for char in c)]


def extract_candidate_words(text, good_tags=set(['JJ', 'JJR', 'JJS', 'NN', 'NNP', 'NNS', 'NNPS'])):
    """
    step 2
    """

    punct = set(string.punctuation)
    stop_words = set(nltk.corpus.stopwords.words('english'))

    tagged_words = itertools.chain.from_iterable(nltk.pos_tag_sents(nltk.word_tokenize(sent) for sent in nltk.sent_tokenize(text)))

    candidates = [word.lower() for word, tag in tagged_words
                  if tag in good_tags and word.lower() not in stop_words
                  and not all(char in punct for char in word)]

    return candidates


@app.route("/services/keywords/extract", methods=("GET",))
def extract():
    """
    http://bdewilde.github.io/blog/2014/09/23/intro-to-automatic-keyphrase-extraction/
    """
    tokens = []
    with open("services/nltk_test.txt", "rU") as input:

        content = input.read()
        phrases = extract_candidate_chunks(content)
        words = extract_candidate_words(content)

        return json.dumps({"phrases": phrases,
                           "words": words})

@app.route("/services/keywords/pattern", methods=("GET",))
def pattern():
    """
    simple pattern matching
    """

    patterns = [
        dict(name="title"),
        dict(name="type", select=["license", "contract"])
    ]

    text = None
    with open("services/nltk_test.txt", 'rU') as input:
        text = input.read()

    if not text:
        raise Exception("empty input text data")

    sentences = nltk.sent_tokenize(text)
    tokenized_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
    tagged_sentences = [nltk.pos_tag(sentence) for sentence in tokenized_sentences]
    chunked_sentences = nltk.ne_chunk_sents(tagged_sentences, binary=True)

    def extract_entity_names(t):
        entity_names = []

        if hasattr(t, 'node') and t.node:
            if t.node == 'NNP':
                entity_names.append(' '.join([child[0] for child in t]))
            else:
                for child in t:
                    entity_names.extend(extract_entity_names(child))
        return entity_names

    entity_names = []
    for tree in chunked_sentences:
        entity_names.extend(extract_entity_names(tree))
    return json.dumps({'data': entity_names})

if __name__ == "__main__":
    service = SERVICES['nltk']
    app.run(service['host'], service['port'], debug=True)
