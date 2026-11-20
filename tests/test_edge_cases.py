# -*- coding: utf-8 -*-
"""Edge-case and regression tests (CJK boundaries, full-width, empty inputs)."""

from src import match_quota, QUOTA_DB, validate_db
from src.preprocessing import normalize_query, tokenize
from src.similarity import (cosine_similarity, extract_dimensions,
                            extract_parameters, parameter_match_score)
from src.tfidf import compute_idf, compute_tfidf_vector


def test_cjk_ascii_boundary_mortar():
    assert extract_parameters("混合砂浆M5")["mortar_grade"] == "M5"


def test_cjk_ascii_boundary_concrete():
    assert extract_parameters("混凝土C30")["concrete_strength"] == "C30"


def test_fullwidth_digits_normalize():
    assert "50mm" in normalize_query("保温板５公分")
    assert "平方米" in normalize_query("１００㎡")


def test_hard_conflict_demotes_incompatible():
    results = match_quota("370mm实心砖墙 M5混合砂浆", top_k=5)
    ids = [r["quota"]["id"] for r in results]
    assert ids[0] == "4-1-8"


def test_no_confident_match_for_nonsense():
    assert match_quota("的 的 的", top_k=3) == []


def test_unknown_token_kept_not_dropped():
    assert compute_tfidf_vector(["x"], {})["x"] == 1.0


def test_empty_vector_division_safe():
    assert cosine_similarity({}, {}) == 0.0
    assert compute_tfidf_vector([], {}) == {}
    assert compute_idf([]) == {}


def test_nonstring_inputs_safe():
    assert normalize_query(None) == ""
    assert tokenize(None) == []
    assert extract_dimensions(None) == {}
    assert extract_parameters(None)["concrete_strength"] is None
    assert parameter_match_score(None, None) == 0.0


def test_db_integrity():
    assert validate_db() == []
    assert len(QUOTA_DB) == 202
