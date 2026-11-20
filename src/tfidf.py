# -*- coding: utf-8 -*-
"""TF-IDF feature extraction.

Implements the core term-frequency / inverse-document-frequency weighting
used to convert token sequences into sparse weight vectors.
"""

import math
from collections import Counter


def compute_idf(documents):
    """Compute IDF for every term across a list of tokenized documents.

    Uses smoothed IDF: ``log((n + 1) / (df + 1)) + 1``.
    """
    n = len(documents)
    df = Counter()
    for doc in documents:
        for word in set(doc):
            df[word] += 1
    return {w: math.log((n + 1) / (df[w] + 1)) + 1 for w in df}


def compute_tfidf_vector(tokens, idf):
    """Compute the TF-IDF weight vector for a token sequence.

    ``idf`` is a dict mapping term -> precomputed IDF weight. Terms not
    present in ``idf`` receive a default weight of 1.
    """
    n = len(tokens) if tokens else 1
    tf = Counter(tokens)
    vec = {}
    for word, count in tf.items():
        vec[word] = (count / n) * idf.get(word, 1)
    return vec
