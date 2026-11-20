# -*- coding: utf-8 -*-
"""Similarity measures and domain-specific scoring heuristics.

Provides cosine similarity over sparse vectors plus the two heuristic
boosters (dimension match, keyword overlap) used by the matcher.
"""

import math
import re

from .preprocessing import tokenize


def cosine_similarity(vec_a, vec_b):
    """Cosine similarity between two sparse weight vectors."""
    all_w = set(list(vec_a.keys()) + list(vec_b.keys()))
    dot = sum(vec_a.get(w, 0) * vec_b.get(w, 0) for w in all_w)
    na = math.sqrt(sum(v ** 2 for v in vec_a.values())) or 1
    nb = math.sqrt(sum(v ** 2 for v in vec_b.values())) or 1
    return dot / (na * nb) if (na * nb) > 0 else 0


def extract_dimensions(text):
    """Extract key numeric dimensions from a component description."""
    dims = {}
    # Thickness
    m = re.search(r'(\d+)\s*mm', text)
    if m:
        dims['thickness'] = int(m.group(1))
    # Cross-section
    m = re.search(r'(\d+)\s*[xX×]\s*(\d+)', text)
    if m:
        dims['width'], dims['height'] = int(m.group(1)), int(m.group(2))
    # Area
    m = re.search(r'(\d+\.?\d*)\s*(万)?\s*m2|平米|平方米', text)
    if m:
        val = float(m.group(1))
        if m.group(2):
            val *= 10000
        dims['area'] = val
    # Floors
    m = re.search(r'(\d+)\s*层', text)
    if m:
        dims['floors'] = int(m.group(1))
    # Count
    m = re.search(r'(\d+)\s*(部|处|套|栋|根|道|个|座|樘)', text)
    if m:
        dims['count'] = int(m.group(1))
    return dims


def dimension_match_score(query_text, quota_text):
    """Dimension-match bonus in the range [0, 0.3]."""
    q_dim = extract_dimensions(query_text)
    q_dim2 = extract_dimensions(quota_text)
    score = 0.0
    all_keys = set(list(q_dim.keys()) + list(q_dim2.keys()))
    matches = 0
    for k in all_keys:
        if k in q_dim and k in q_dim2:
            v1, v2 = q_dim[k], q_dim2[k]
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                if v2 > 0:
                    ratio = min(v1, v2) / max(v1, v2)
                    if ratio > 0.7:
                        matches += 1
                    score += ratio * 0.06
    return min(score, 0.3)


def keyword_boost(query_tokens, quota_text):
    """Keyword-overlap bonus in the range [0, 0.2].

    Strong engineering terms contribute twice the weight of ordinary terms.
    """
    quota_tokens = set(tokenize(quota_text))
    query_set = set(query_tokens)
    overlap = query_set & quota_tokens
    strong = {'构造柱', '圈梁', '实心砖', '加气混凝土', 'XPS', 'SBS', '断桥', '扶手',
              '无障碍', '电梯', '钢结构', '保温', '防水', '抹灰', '真石漆', '电伴热'}
    boost = sum(2.0 if w in strong else 1.0 for w in overlap)
    return min(boost * 0.025, 0.2)
