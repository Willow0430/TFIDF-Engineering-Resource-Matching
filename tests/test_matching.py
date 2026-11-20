# -*- coding: utf-8 -*-
"""Tests for the matching engine and change-cost prediction."""

from src import QUOTA_DB, match_quota, predict_change, run_full_tests


def test_quota_db_size():
    assert len(QUOTA_DB) == 202
    assert len(set(q["category"] for q in QUOTA_DB)) == 21


def test_match_quota_returns_ranked_results():
    results = match_quota("370mm实心砖墙 M5混合砂浆", top_k=3)
    assert results, "expected at least one match"
    assert results[0]["quota"]["category"] == "砌筑工程"
    # Sorted by combined score, descending
    combined = [r["combined"] for r in results]
    assert combined == sorted(combined, reverse=True)


def test_match_quota_result_structure():
    results = match_quota("C25现浇混凝土构造柱 240x240", top_k=1)
    assert results
    r = results[0]
    for key in ("quota", "tfidf_sim", "kw_score", "dim_score",
                "combined", "confidence", "reliability"):
        assert key in r


def test_predict_change_structure():
    p = predict_change("扶手加装", 350, "不锈钢扶手D38")
    for key in ("predicted_level", "predicted_amount", "confidence",
                "risk_tag", "risk_color", "top_matches"):
        assert key in p


def test_full_evaluation_accuracy():
    results = run_full_tests(verbose=False)
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    standard = [r for r in results if r["note"].startswith("标准")]
    colloquial = [r for r in results if r["note"].startswith("口语")]

    assert total == 30
    assert correct / total >= 0.90
    assert sum(1 for r in standard if r["correct"]) == len(standard)  # standard = 100%
    assert sum(1 for r in colloquial if r["correct"]) / len(colloquial) >= 0.80
