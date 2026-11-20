# -*- coding: utf-8 -*-
"""Tests for the evaluation suite and ablation study."""

import os
import tempfile

from src import (QUOTA_DB, CATEGORIES, LABELED_TEST_CASES, run_full_tests,
                 run_ablation)
from src.evaluation import (ABLATION_CONFIGS, topk_accuracy, precision_at_k,
                            recall_at_k, mean_reciprocal_rank)

ALL_IDS = {q["id"] for q in QUOTA_DB}


def _mk(cat, qid):
    return {"quota": {"category": cat, "id": qid}}


def test_labeled_cases_present():
    assert len(LABELED_TEST_CASES) == 30


def test_labeled_cases_well_formed():
    for c in LABELED_TEST_CASES:
        for key in ("query", "category", "ids", "note", "ambiguous", "verified"):
            assert key in c
        assert c["category"] in CATEGORIES
        assert c["ids"], "empty ids for %s" % c["note"]
        for qid in c["ids"]:
            assert qid in ALL_IDS, "unknown id %s in %s" % (qid, c["note"])


def test_ablation_configs_sum_to_one():
    for name, w in ABLATION_CONFIGS.items():
        assert abs(sum(w) - 1.0) < 1e-9, name


def test_run_full_tests_returns_summary_and_cases():
    summary, per_case = run_full_tests(verbose=False)
    for key in ("n_cases", "category_top1", "category_top3", "id_top1",
                "id_top3", "precision@1", "recall@3", "mrr"):
        assert key in summary
    assert summary["n_cases"] == 30
    assert len(per_case) == 30
    assert 0.0 <= summary["category_top1"] <= 1.0
    assert 0.0 <= summary["mrr"] <= 1.0


def test_run_ablation_four_rows():
    rows = run_ablation(verbose=False)
    assert len(rows) == 4
    names = [name for name, _ in rows]
    assert names == list(ABLATION_CONFIGS.keys())


def test_metrics_on_synthetic_cases():
    cases = [
        {"matches": [_mk("A", "1"), _mk("A", "2")],
         "expected_category": "A", "ids": ["2"]},
        {"matches": [_mk("B", "3")],
         "expected_category": "B", "ids": ["3"]},
    ]
    assert abs(topk_accuracy(cases, "category", 1) - 1.0) < 1e-9
    assert abs(topk_accuracy(cases, "id", 1) - 0.5) < 1e-9
    assert abs(topk_accuracy(cases, "id", 3) - 1.0) < 1e-9
    assert abs(precision_at_k(cases, 1) - 0.5) < 1e-9
    assert abs(recall_at_k(cases, 3) - 1.0) < 1e-9
    assert abs(mean_reciprocal_rank(cases, 3) - 0.75) < 1e-9


def test_csv_export():
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "results.csv")
    run_full_tests(verbose=False, csv_path=path)
    assert os.path.exists(path)
    with open(path, encoding="utf-8-sig") as f:
        header = f.readline()
    assert "查询" in header
