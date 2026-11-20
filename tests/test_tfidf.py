# -*- coding: utf-8 -*-
"""Tests for TF-IDF feature extraction."""

import math

from src.tfidf import compute_idf, compute_tfidf_vector


def test_compute_idf_smoothed():
    idf = compute_idf([["a", "b"], ["a", "c"]])
    # a appears in both documents -> df=2 -> idf = log(3/3)+1 = 1
    assert math.isclose(idf["a"], 1.0, rel_tol=1e-9)
    # b appears once -> df=1 -> idf = log(3/2)+1
    assert math.isclose(idf["b"], math.log(1.5) + 1, rel_tol=1e-9)


def test_compute_tfidf_vector():
    vec = compute_tfidf_vector(["a", "a", "b"], {"a": 1.0, "b": 2.0})
    assert math.isclose(vec["a"], (2 / 3) * 1.0, rel_tol=1e-9)
    assert math.isclose(vec["b"], (1 / 3) * 2.0, rel_tol=1e-9)


def test_compute_tfidf_vector_default_idf():
    # Unknown terms default to idf=1
    vec = compute_tfidf_vector(["x"], {})
    assert vec["x"] == 1.0


def test_compute_tfidf_vector_empty():
    assert compute_tfidf_vector([], {}) == {}
