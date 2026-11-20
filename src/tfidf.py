# -*- coding: utf-8 -*-
"""TF-IDF feature extraction.

Converts token sequences into sparse TF-IDF weight vectors.

Vector-space invariant: queries and resource documents MUST be projected with
the same ``idf`` table (built once over the resource corpus in ``matching``),
otherwise cosine similarities are not comparable.

Domain dictionary and stopword filtering live in ``preprocessing``; this module
only performs the weighted feature extraction:

- Smoothed IDF: ``log((n + 1) / (df + 1)) + 1``.
- Terms absent from ``idf`` (out-of-vocabulary / unknown words) receive a
  default weight instead of being dropped, so a novel query term still counts.
- Empty token lists yield an empty vector (never divide by zero).
"""

import math
from collections import Counter


def compute_idf(documents):
    """Compute IDF for every term across a list of tokenized documents.

    Uses smoothed IDF: ``log((n + 1) / (df + 1)) + 1``. An empty corpus
    returns an empty mapping.
    """
    n = len(documents)
    if n == 0:
        return {}
    df = Counter()
    for doc in documents:
        for word in set(doc):
            df[word] += 1
    return {w: math.log((n + 1) / (df[w] + 1)) + 1 for w in df}


def compute_tfidf_vector(tokens, idf, default_idf=1.0):
    """Compute the TF-IDF weight vector for a token sequence.

    ``idf`` is a dict mapping term -> precomputed IDF weight. Terms not present
    in ``idf`` receive ``default_idf`` (kept, not dropped). An empty ``tokens``
    yields an empty vector.
    """
    if not tokens:
        return {}
    n = len(tokens)
    tf = Counter(tokens)
    return {word: (count / n) * idf.get(word, default_idf)
            for word, count in tf.items()}
