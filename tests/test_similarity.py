# -*- coding: utf-8 -*-
"""Tests for similarity measures and engineering-parameter scoring."""

import math

from src.similarity import (cosine_similarity, extract_dimensions,
                            extract_parameters, parameter_match_score,
                            keyword_match)


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


def test_extract_dimensions_nonstring():
    assert extract_dimensions("") == {}
    assert extract_dimensions(None) == {}


def test_extract_parameters_strength():
    p = extract_parameters("C25混凝土 混合砂浆M5 HRB400钢筋")
    assert p["concrete_strength"] == "C25"
    assert p["mortar_grade"] == "M5"
    assert p["rebar_grade"] == "HRB400"


def test_extract_parameters_cjk_boundary():
    # No word boundary between 浆 and M; lookarounds must still catch it.
    assert extract_parameters("混合砂浆M5")["mortar_grade"] == "M5"


def test_parameter_match_neutral_when_no_params():
    assert parameter_match_score("一个描述", "另一个描述") == 0.0


def test_parameter_match_hard_conflict():
    # 370mm query vs 240mm resource -> hard conflict.
    assert parameter_match_score("370mm砖墙", "实心砖墙 厚度240mm") == -0.6


def test_parameter_match_in_range():
    s = parameter_match_score("370mm砖墙", "实心砖墙 厚度370mm 混合砂浆M5")
    assert -1.0 <= s <= 1.0


def test_keyword_match_in_range():
    tokens = ["实心砖墙", "混合砂浆"]
    s = keyword_match(tokens, "实心砖墙 厚度370mm 混合砂浆M5")
    assert 0.0 <= s <= 1.0
    assert s > 0.0
