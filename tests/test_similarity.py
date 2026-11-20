# -*- coding: utf-8 -*-
"""Tests for similarity measures and dimension extraction."""

import math

from src.similarity import (cosine_similarity, extract_dimensions,
                            dimension_match_score, keyword_boost)


def test_cosine_identical():
    assert math.isclose(cosine_similarity({"a": 1, "b": 1}, {"a": 1, "b": 1}), 1.0)


def test_cosine_orthogonal():
    assert cosine_similarity({"a": 1}, {"b": 1}) == 0.0


def test_cosine_empty():
    assert cosine_similarity({}, {}) == 0.0


def test_extract_dimensions_thickness():
    assert extract_dimensions("厚度120mm")["thickness"] == 120


def test_extract_dimensions_section():
    dims = extract_dimensions("240x240 构造柱")
    assert dims["width"] == 240
    assert dims["height"] == 240


def test_dimension_match_score_in_range():
    score = dimension_match_score("370mm砖墙", "实心砖墙 厚度370mm")
    assert 0.0 <= score <= 0.3


def test_keyword_boost_in_range():
    tokens = ["实心砖墙", "混合砂浆"]
    score = keyword_boost(tokens, "实心砖墙 厚度370mm 混合砂浆M5")
    assert 0.0 <= score <= 0.2
