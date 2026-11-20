# -*- coding: utf-8 -*-
"""Tests for the matching engine and change-cost prediction."""

from src import QUOTA_DB, match_quota, predict_change, rebuild_index, validate_db


def test_quota_db_size():
    assert len(QUOTA_DB) == 202
    assert len(set(q["category"] for q in QUOTA_DB)) == 21


def test_validate_db_clean():
    assert validate_db() == []


def test_rebuild_index_nonempty():
    idf = rebuild_index()
    assert len(idf) > 0


def test_match_quota_returns_ranked_results():
    results = match_quota("370mm实心砖墙 M5混合砂浆", top_k=3)
    assert results, "expected at least one match"
    assert results[0]["quota"]["category"] == "砌筑工程"
    combined = [r["combined"] for r in results]
    assert combined == sorted(combined, reverse=True)


def test_match_quota_result_structure():
    results = match_quota("C25现浇混凝土构造柱 240x240", top_k=1)
    assert results
    r = results[0]
    for key in ("quota", "s_text", "s_keyword", "s_param", "s_category",
                "combined", "confidence", "reliability", "explanation"):
        assert key in r


def test_match_quota_weights_override():
    results = match_quota("370mm实心砖墙 M5混合砂浆", top_k=3,
                          weights=(1.0, 0.0, 0.0, 0.0))
    assert results


def test_match_quota_empty_query():
    assert match_quota("") == []
    assert match_quota("的") == []


def test_predict_change_structure():
    p = predict_change("扶手加装", 350, "不锈钢扶手D38")
    for key in ("predicted_level", "predicted_amount", "confidence",
                "risk_tag", "risk_color", "top_matches"):
        assert key in p
