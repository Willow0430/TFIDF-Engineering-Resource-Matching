# -*- coding: utf-8 -*-
"""Matching engine and change-cost prediction.

``match_quota`` fuses three signals into a single score:

- TF-IDF cosine similarity (weight 0.65)
- keyword-overlap boost       (weight 0.20)
- dimension-match boost       (weight 0.15)
"""

from collections import defaultdict

from .preprocessing import normalize_query, tokenize
from .similarity import cosine_similarity, dimension_match_score, keyword_boost
from .tfidf import compute_idf, compute_tfidf_vector
from .quota_db import QUOTA_DB

# ── Pre-compute IDF over the entire resource corpus ──
_QUOTA_TEXTS = [q["_text"] for q in QUOTA_DB]
_ALL_TOKENS = [tokenize(t) for t in _QUOTA_TEXTS]
IDF = compute_idf(_ALL_TOKENS)


def match_quota(query_text, top_k=5):
    """Match a query against the resource library and return the top matches.

    Each result carries the matched resource, the three component scores,
    the combined score, a percentage confidence and a reliability label.
    """
    normalized = normalize_query(query_text)
    tokens = tokenize(normalized)
    query_vec = compute_tfidf_vector(tokens, IDF)

    results = []
    for item in QUOTA_DB:
        item_tokens = tokenize(item["_text"])
        item_vec = compute_tfidf_vector(item_tokens, IDF)

        # TF-IDF cosine similarity (weight 0.65)
        tfidf_sim = cosine_similarity(query_vec, item_vec)

        # Keyword-overlap boost (weight 0.20)
        kw_score = keyword_boost(tokens, item["_text"])

        # Dimension-match boost (weight 0.15)
        dim_score = dimension_match_score(normalized, item["_text"])

        combined = tfidf_sim * 0.65 + kw_score * 0.20 + dim_score * 0.15

        if combined > 0.03:
            results.append({
                "quota": item,
                "tfidf_sim": tfidf_sim,
                "kw_score": kw_score,
                "dim_score": dim_score,
                "combined": combined,
                "confidence": min(combined * 100, 99.9),
                "reliability": "high" if combined > 0.25 else ("medium" if combined > 0.12 else "low"),
            })

    results.sort(key=lambda x: x["combined"], reverse=True)
    return results[:top_k]


# ── Change-cost prediction training samples ──
CHANGE_TRAINING = [
    {"type": "扶手加装", "area": 80, "amount": 12, "level": "小额<50万"},
    {"type": "扶手加装", "area": 350, "amount": 52, "level": "中额50-200万"},
    {"type": "扶手加装", "area": 800, "amount": 180, "level": "中额50-200万"},
    {"type": "管线迁改", "area": 150, "amount": 55, "level": "中额50-200万"},
    {"type": "管线迁改", "area": 500, "amount": 210, "level": "大额>200万"},
    {"type": "管线迁改", "area": 1200, "amount": 320, "level": "大额>200万"},
    {"type": "外墙涂料变更", "area": 300, "amount": 8, "level": "小额<50万"},
    {"type": "外墙涂料变更", "area": 1200, "amount": 35, "level": "小额<50万"},
    {"type": "外墙涂料变更", "area": 500, "amount": -12, "level": "节约"},
    {"type": "门窗更换", "area": 80, "amount": 28, "level": "小额<50万"},
    {"type": "门窗更换", "area": 250, "amount": 95, "level": "中额50-200万"},
    {"type": "电梯加装", "area": 45, "amount": 180, "level": "中额50-200万"},
    {"type": "电梯加装", "area": 65, "amount": 275, "level": "大额>200万"},
    {"type": "道路拓宽", "area": 400, "amount": 65, "level": "中额50-200万"},
    {"type": "绿化提升", "area": 500, "amount": 22, "level": "小额<50万"},
    {"type": "绿化提升", "area": 2000, "amount": 85, "level": "中额50-200万"},
    {"type": "结构加固", "area": 150, "amount": 280, "level": "大额>200万"},
    {"type": "结构加固", "area": 350, "amount": 550, "level": "大额>200万"},
    {"type": "广场变更", "area": 400, "amount": 180, "level": "中额50-200万"},
    {"type": "广场变更", "area": 800, "amount": 550, "level": "大额>200万"},
    {"type": "保温增加", "area": 2000, "amount": 105, "level": "中额50-200万"},
    {"type": "防水翻新", "area": 1500, "amount": 45, "level": "小额<50万"},
    {"type": "基础超挖", "area": 100, "amount": 150, "level": "中额50-200万"},
    {"type": "基础超挖", "area": 250, "amount": 320, "level": "大额>200万"},
]

_LEVELS = {
    "节约": ("[节约]", '#4CAF50'),
    "小额<50万": ("[低风险]", '#FF9800'),
    "中额50-200万": ("[中风险]", '#F44336'),
    "大额>200万": ("[高风险]", '#B71C1C'),
}


def predict_change(query_type, area, component=""):
    """Predict change-cost band and amount using TF-IDF similarity.

    Blends text similarity (weight 0.55) with an area-proximity factor
    (weight 0.45), then performs a weighted vote over the top-5 samples.
    """
    query = f"{query_type} {area}平方米 {component}"
    q_tokens = tokenize(normalize_query(query))
    q_vec = compute_tfidf_vector(q_tokens, IDF)

    scores = []
    for s in CHANGE_TRAINING:
        s_text = f"{s['type']} {s['area']}平方米"
        s_tokens = tokenize(s_text)
        s_vec = compute_tfidf_vector(s_tokens, IDF)
        text_sim = cosine_similarity(q_vec, s_vec)
        area_factor = 1 - abs(area - s['area']) / max(area, s['area'], 1)
        combined = text_sim * 0.55 + area_factor * 0.45
        scores.append({"sample": s, "score": combined})

    scores.sort(key=lambda x: x["score"], reverse=True)
    top = scores[:5]

    level_weight = defaultdict(float)
    amount_sum = 0
    weight_sum = 0
    for t in top:
        w = t["score"]
        level_weight[t["sample"]["level"]] += w
        amount_sum += t["sample"]["amount"] * w
        weight_sum += w
    predicted_level = max(level_weight, key=level_weight.get)
    predicted_amount = amount_sum / weight_sum if weight_sum > 0 else 0
    confidence = top[0]["score"] if top else 0

    risk_tag, risk_color = _LEVELS.get(predicted_level, ("[未知]", '#666666'))

    return {"predicted_level": predicted_level, "predicted_amount": predicted_amount,
            "confidence": confidence, "risk_tag": risk_tag, "risk_color": risk_color,
            "top_matches": [{"type": t["sample"]["type"], "area": t["sample"]["area"],
                             "amount": t["sample"]["amount"], "score": t["score"]} for t in top[:3]]}
