# -*- coding: utf-8 -*-
"""Similarity measures and engineering-parameter scoring.

Provides:
- ``cosine_similarity`` over sparse weight vectors.
- ``extract_dimensions`` / ``extract_parameters``: structured, unit-normalized
  extraction of dimensions (thickness, cross-section, area, volume, floors,
  count, diameter) and strength/material parameters (concrete grade, mortar
  grade, rebar grade, material type).
- ``parameter_match_score``: query-driven parameter matching with a hard
  conflict penalty for incompatible specifications, plus quantity / material
  signals.
- ``keyword_match``: weighted keyword-overlap ratio in [0, 1].
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


def _to_float(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _to_int(s):
    v = _to_float(s)
    return int(v) if v is not None else None


def extract_dimensions(text):
    """Extract numeric dimensions from a description, unit-normalized.

    Never raises on malformed input; missing keys are simply absent.
    """
    if not isinstance(text, str):
        return {}
    dims = {}

    # Thickness (bare "Nmm" or "厚度Nmm").
    m = re.search(r'(?:厚度\s*)?(\d+(?:\.\d+)?)\s*mm', text)
    if m:
        v = _to_float(m.group(1))
        if v is not None:
            dims['thickness'] = v

    # Cross-section "WxH".
    m = re.search(r'(\d+(?:\.\d+)?)\s*[xX×*]\s*(\d+(?:\.\d+)?)', text)
    if m:
        w, h = _to_float(m.group(1)), _to_float(m.group(2))
        if w is not None and h is not None:
            dims['width'], dims['height'] = w, h

    # Diameter (直径N / ΦN / DN).
    m = re.search(r'(?:直径\s*|[Φφ]|D)(\d+(?:\.\d+)?)', text)
    if m:
        v = _to_float(m.group(1))
        if v is not None:
            dims['diameter'] = v

    # Area (万 handled as x10000).
    m = re.search(r'(\d+(?:\.\d+)?)\s*(万)?\s*(?:平方米|㎡|m²|m2|平米)', text)
    if m:
        v = _to_float(m.group(1))
        if v is not None:
            if m.group(2):
                v *= 10000
            dims['area'] = v

    # Volume.
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:立方米|m³|m3)', text)
    if m:
        v = _to_float(m.group(1))
        if v is not None:
            dims['volume'] = v

    # Floors.
    m = re.search(r'(\d+)\s*层', text)
    if m:
        dims['floors'] = _to_int(m.group(1))

    # Count / quantity.
    m = re.search(r'(\d+(?:\.\d+)?)\s*(部|处|套|栋|根|道|个|座|樘|棵|株)', text)
    if m:
        v = _to_float(m.group(1))
        if v is not None:
            dims['count'] = v

    return dims


# Material-type keywords whose mismatch is meaningful (XPS vs EPS, SBS vs JS).
MATERIAL_TERMS = {
    '挤塑聚苯板', 'xps', 'eps', '岩棉', '真石漆', '乳胶漆', '断桥铝合金',
    '塑钢', '不锈钢', '碳纤维', 'sbs', 'js', '渗透结晶', '透水砖',
    '花岗岩', '大理石', '矿棉板', '硅酸钙板', '实心砖', '加气混凝土',
    '陶粒', '多孔砖', '空心砖', '浆砌片石', '水泥基', '聚合物',
}


def extract_parameters(text):
    """Extract strength grades and material types from a description."""
    if not isinstance(text, str):
        return {'concrete_strength': None, 'mortar_grade': None,
                'rebar_grade': None, 'materials': set()}

    m = re.search(r'(?<![A-Za-z0-9])C(\d{2})(?![A-Za-z0-9])', text, re.IGNORECASE)
    concrete = ('C' + m.group(1)) if m else None

    m = re.search(r'(?<![A-Za-z0-9])M(\d+(?:\.\d+)?)(?![A-Za-z0-9])', text, re.IGNORECASE)
    mortar = None
    if m and m.group(0).lower() not in ('m2', 'm3'):
        mortar = 'M' + m.group(1)

    m = re.search(r'(?<![A-Za-z0-9])(HPB300|HRB335|HRB400|HRB500)(?![A-Za-z0-9])', text, re.IGNORECASE)
    rebar = m.group(1).upper() if m else None

    low = text.lower()
    materials = {t for t in MATERIAL_TERMS if t in low}
    return {'concrete_strength': concrete, 'mortar_grade': mortar,
            'rebar_grade': rebar, 'materials': materials}


# Strict specification parameters: exact match required, mismatch = conflict.
_SPEC_DIM_KEYS = ('thickness', 'diameter', 'width', 'height')
_STRENGTH_KEYS = ('concrete_strength', 'mortar_grade', 'rebar_grade')
# Loose quantity parameters: ratio-based, no hard conflict.
_QTY_DIM_KEYS = ('area', 'volume', 'floors', 'count')

_HARD_CONFLICT = -0.6
_MISSING_PENALTY = -0.15


def _spec_equal(a, b):
    return a == b


def _quantity_sim(a, b):
    """Loose ratio-based similarity for quantities in [0, 1]."""
    if a is None or b is None:
        return 0.0
    try:
        ratio = min(a, b) / max(a, b)
    except (TypeError, ZeroDivisionError):
        return 0.0
    return max(0.0, min(1.0, ratio))


def parameter_match_score(query_text, quota_text):
    """Score how well a resource satisfies the query's engineering parameters.

    Returns a value in [-1, 1]:

    - A hard conflict on any *specification* parameter (thickness, cross-section,
      diameter, concrete/mortar/rebar grade) returns a strong negative score so
      that a textually-similar but dimensionally-incompatible resource is
      demoted.
    - Otherwise, per-requirement contributions are averaged (spec match +1,
      missing spec -0.15, quantity ratio in [0,1], material overlap in [0,1]).
    - A query with no parameters yields 0.0 (neutral).
    """
    qd = extract_dimensions(query_text)
    rd = extract_dimensions(quota_text)
    qp = extract_parameters(query_text)
    rp = extract_parameters(quota_text)

    # Hard conflict detection on strict spec params.
    for key in _SPEC_DIM_KEYS:
        if key in qd and key in rd and not _spec_equal(qd[key], rd[key]):
            return _HARD_CONFLICT
    for key in _STRENGTH_KEYS:
        if qp[key] and rp[key] and qp[key] != rp[key]:
            return _HARD_CONFLICT

    contributions = []

    for key in _SPEC_DIM_KEYS:
        if key in qd:
            contributions.append(1.0 if (key in rd and _spec_equal(qd[key], rd[key])) else _MISSING_PENALTY)
    for key in _STRENGTH_KEYS:
        if qp[key]:
            contributions.append(1.0 if rp[key] == qp[key] else _MISSING_PENALTY)
    for key in _QTY_DIM_KEYS:
        if key in qd:
            contributions.append(_quantity_sim(qd[key], rd.get(key)) if key in rd else 0.0)
    if qp['materials']:
        if rp['materials']:
            contributions.append(len(qp['materials'] & rp['materials']) / len(qp['materials']))
        else:
            contributions.append(_MISSING_PENALTY)

    if not contributions:
        return 0.0
    return max(-1.0, min(1.0, sum(contributions) / len(contributions)))


# Strong engineering terms contribute twice the weight of ordinary terms.
STRONG_TERMS = {
    '构造柱', '圈梁', '实心砖', '加气混凝土', 'xps', 'eps', 'sbs', 'js',
    '断桥', '扶手', '无障碍', '电梯', '钢结构', '保温', '防水', '抹灰',
    '真石漆', '乳胶漆', '电伴热', '透水砖', '水稳', '沥青', '植筋',
    '渗透结晶', '防水卷材', '防水涂料', '防火门', '平开窗', '塑钢',
}


def keyword_match(query_tokens, quota_text):
    """Weighted keyword-overlap ratio in [0, 1]."""
    quota_tokens = set(tokenize(quota_text))
    query_set = set(query_tokens)
    if not query_set:
        return 0.0
    overlap = query_set & quota_tokens
    weight = sum(2.0 if w in STRONG_TERMS else 1.0 for w in overlap)
    max_weight = sum(2.0 if w in STRONG_TERMS else 1.0 for w in query_set)
    return weight / max_weight if max_weight > 0 else 0.0
