# -*- coding: utf-8 -*-
"""Tests for text preprocessing (normalization + tokenization)."""

from src.preprocessing import normalize_query, tokenize


def test_normalize_colloquial_unit():
    assert normalize_query("5公分") == "50mm"
    assert normalize_query("3公分") == "30mm"


def test_normalize_thickness_notation():
    assert "370mm" in normalize_query("实心砖墙370厚")


def test_normalize_floor_numerals():
    assert "7层" in normalize_query("七层砖混住宅")
    assert normalize_query("一楼") == "首层"


def test_normalize_fullwidth():
    assert "50mm" in normalize_query("保温板５公分")


def test_normalize_unit_unify():
    assert "平方米" in normalize_query("100㎡")
    assert "平方米" in normalize_query("100平米")


def test_normalize_empty_and_nonstring():
    assert normalize_query("") == ""
    assert normalize_query("   ") == ""
    assert normalize_query(None) == ""
    assert normalize_query(123) == ""


def test_normalize_keeps_parameters():
    out = normalize_query("HRB400钢筋 C25 M5 370mm")
    assert "HRB400" in out
    assert "C25" in out
    assert "M5" in out


def test_tokenize_unit_pairs():
    assert "120mm" in tokenize("120mm")


def test_tokenize_nonempty():
    assert len(tokenize("实心砖墙 混合砂浆")) > 0


def test_tokenize_empty():
    assert tokenize("") == []
    assert tokenize(None) == []
    assert tokenize("的") == []


def test_tokenize_extracts_grades():
    tokens = tokenize("HRB400钢筋 C25 M5")
    assert "hrb400" in tokens
    assert "c25" in tokens
    assert "m5" in tokens
