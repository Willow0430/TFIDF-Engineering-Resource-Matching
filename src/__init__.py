# -*- coding: utf-8 -*-
"""TFIDF-Engineering-Resource-Matching.

A TF-IDF based engineering resource semantic-matching library. Turns
free-form (often colloquial) Chinese engineering descriptions into TF-IDF
vectors and ranks candidate resources via fused cosine / keyword /
dimension scoring.
"""

from .preprocessing import normalize_query, tokenize
from .tfidf import compute_idf, compute_tfidf_vector
from .similarity import (cosine_similarity, extract_dimensions, extract_parameters,
                         parameter_match_score, keyword_match)
from .quota_db import (QUOTA_DB, build_quota_db, validate_db,
                       DATA_SOURCE, LAST_UPDATED, CATEGORIES)
from .matching import match_quota, predict_change, IDF, CHANGE_TRAINING, rebuild_index
from .evaluation import LABELED_TEST_CASES, run_full_tests, run_ablation, demonstrate

__version__ = "3.0.0"

__all__ = [
    "normalize_query", "tokenize",
    "compute_idf", "compute_tfidf_vector",
    "cosine_similarity", "extract_dimensions", "extract_parameters",
    "parameter_match_score", "keyword_match",
    "QUOTA_DB", "build_quota_db", "validate_db",
    "DATA_SOURCE", "LAST_UPDATED", "CATEGORIES",
    "match_quota", "predict_change", "IDF", "CHANGE_TRAINING", "rebuild_index",
    "LABELED_TEST_CASES", "run_full_tests", "run_ablation", "demonstrate",
]
