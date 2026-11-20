# -*- coding: utf-8 -*-
"""Tests for text preprocessing (normalization + tokenization)."""

from src.preprocessing import normalize_query, tokenize


def test_normalize_colloquial_unit():
    assert normalize_query("5公分") == "50mm"
    assert normalize_query("3公分") == "30mm"


def test_normalize_colloquial_term():
    assert "挤塑聚苯板" in normalize_query("保温板5公分")
    assert normalize_query("一楼") == "首层"


def test_normalize_thickness_notation():
    # "370厚" -> "370mm" (but "厚度" should NOT be rewritten)
    assert "370mm" in normalize_query("实心砖墙370厚")


def test_tokenize_extracts_unit_pairs():
    tokens = tokenize("120mm")
    assert "120mm" in tokens


def test_tokenize_returns_nonempty_tokens():
    assert len(tokenize("实心砖墙 混合砂浆")) > 0
