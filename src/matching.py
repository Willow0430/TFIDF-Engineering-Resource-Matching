# -*- coding: utf-8 -*-
"""Matching engine and change-cost prediction.

``match_quota`` fuses four explainable signals into a single score:

    S = 0.40·S_t + 0.25·S_k + 0.25·S_d + 0.10·S_c

- ``S_t``  text similarity     (TF-IDF cosine)          weight 0.40
- ``S_k``  keyword overlap     (weighted term overlap)  weight 0.25
- ``S_d``  parameter match     (dimension / material / strength, with
                                  conflict penalty)     weight 0.25
- ``S_c``  category affinity   (specialty-keyword hit)  weight 0.10

These weights are an *experimental starting point* and must be tuned on a
held-out labeled set; they are not claimed to be optimal.
"""

from collections import defaultdict

from .preprocessing import normalize_query, tokenize
from .similarity import cosine_similarity, keyword_match, parameter_match_score
from .tfidf import compute_idf, compute_tfidf_vector
from .quota_db import QUOTA_DB

# ── Pre-compute IDF over the entire resource corpus ──


def rebuild_index():
    """Recompute the module-level IDF table from the current ``QUOTA_DB``.

    Call this after the resource library is replaced (e.g. loaded from a CSV)
    so that queries and documents still share one vector space.
    """
    global IDF
    texts = [q["_text"] for q in QUOTA_DB]
    IDF = compute_idf([tokenize(t) for t in texts])
    return IDF


IDF = rebuild_index()

# Experimental fusion weights (sum to 1.0). Tune on a validation set.
W_TEXT, W_KEYWORD, W_PARAM, W_CATEGORY = 0.40, 0.25, 0.25, 0.10

# Rejection threshold and reliability bands.
MIN_SCORE = 0.05
HIGH_SCORE = 0.45
MEDIUM_SCORE = 0.20


# Specialty -> indicative keyword set (lowercase), for category affinity.
CATEGORY_KEYWORDS = {
    '砌筑工程': {'砖墙', '砌块', '砌筑', '砖砌', '挡土墙', '实心砖', '多孔砖', '空心砖', '陶粒', '加气混凝土', '台阶'},
    '混凝土工程': {'混凝土', '构造柱', '框架柱', '圈梁', '过梁', '矩形梁', '楼板', '楼梯', '基础', '压顶', '散水', '预制', '空心板', '雨篷'},
    '钢筋工程': {'钢筋', '制安', '植筋', '套筒', '焊接网', '机械连接'},
    '保温工程': {'保温', 'xps', 'eps', '岩棉', '挤塑', '苯板', '隔热'},
    '防水工程': {'防水', 'sbs', 'js', '渗透结晶', '卷材', '防水涂料', '防水层'},
    '抹灰工程': {'抹灰', '找平', '水泥砂浆', '抹面', '抹灰层'},
    '涂料工程': {'涂料', '真石漆', '乳胶漆', '刷漆', '油漆', '批刮'},
    '门窗工程': {'门窗', '断桥', '塑钢', '平开窗', '防盗门', '防火门', '中空玻璃', '推拉窗'},
    '钢结构工程': {'钢结构', '井道', '钢梁', '钢柱', '型钢', '钢架'},
    '楼地面工程': {'楼地面', '地砖', '地板', '踢脚', '地坪', '地面', '找平层'},
    '天棚工程': {'天棚', '吊顶', '龙骨', '矿棉板', '硅酸钙板', '顶棚'},
    '屋面工程': {'屋面', '屋顶', '屋面板', '女儿墙', '檐口'},
    '安装工程': {'管道', '给水', '排水', 'ppr', 'pvc', '水暖', '阀门', '水表'},
    '电气工程': {'电气', '灯具', '照明', '电线', '电缆', '配电', 'led', '开关', '插座'},
    '暖通工程': {'暖通', '采暖', '通风', '空调', '地暖', '散热器', '风机'},
    '市政工程': {'市政', '道路', '沥青', '水稳', '透水砖', '路基', '面层', '路面', '路缘石'},
    '园林景观': {'园林', '景观', '绿化', '种植', '乔木', '灌木', '草坪', '铺装'},
    '适老化专项': {'适老化', '无障碍', '扶手', '坡道', '日间照料', '电伴热', '助浴'},
    '拆除工程': {'拆除', '清运', '破碎', '拆改'},
    '措施项目': {'措施', '脚手架', '模板', '垂直运输', '安全文明', '成品保护'},
    '智能化': {'智能化', '门禁', '监控', '弱电', 'nb-iot', '安防', '综合管沟'},
}


def category_match(query_tokens, category):
    """Category affinity in [0, 1]: 0.5 per hit keyword, capped at 1.0.

    Uses substring containment so that domain-word tokens (e.g. "实心砖墙")
    still match category keywords (e.g. "砖墙").
    """
    kws = CATEGORY_KEYWORDS.get(category)
    if not kws:
        return 0.0
    hits = 0
    for kw in kws:
        if any(kw in tok or tok in kw for tok in query_tokens):
            hits += 1
    return min(1.0, 0.5 * hits)


def _reliability(combined):
    if combined >= HIGH_SCORE:
        return "high"
    if combined >= MEDIUM_SCORE:
        return "medium"
    return "low"


def match_quota(query_text, top_k=5, weights=None):
    """Match a query against the resource library.

    Returns up to ``top_k`` results (each with the four component scores, the
    combined score, a percentage confidence, a reliability label and a human
    explanation). Candidates whose combined score is below ``MIN_SCORE`` are
    rejected; an empty list therefore means "no confident match".

    ``weights`` optionally overrides the fusion weights as a 4-tuple
    ``(w_text, w_keyword, w_param, w_category)``; this is used by the ablation
    study to measure each signal's marginal contribution. ``None`` uses the
    module defaults.
    """
    w_text, w_keyword, w_param, w_category = (
        weights if weights is not None
        else (W_TEXT, W_KEYWORD, W_PARAM, W_CATEGORY)
    )

    normalized = normalize_query(query_text)
    tokens = tokenize(normalized)
    if not tokens:
        return []
    query_vec = compute_tfidf_vector(tokens, IDF)

    results = []
    for item in QUOTA_DB:
        item_tokens = tokenize(item["_text"])
        item_vec = compute_tfidf_vector(item_tokens, IDF)

        s_text = cosine_similarity(query_vec, item_vec)
        s_keyword = keyword_match(tokens, item["_text"])
        s_param = parameter_match_score(normalized, item["_text"])
        s_category = category_match(tokens, item["category"])

        combined = (w_text * s_text + w_keyword * s_keyword +
                    w_param * s_param + w_category * s_category)

        if combined <= MIN_SCORE:
            continue

        results.append({
            "quota": item,
            "s_text": s_text,
            "s_keyword": s_keyword,
            "s_param": s_param,
            "s_category": s_category,
            "combined": combined,
            "confidence": min(max(combined, 0.0) * 100, 99.9),
            "reliability": _reliability(combined),
            "explanation": (
                f"文本 {s_text:.3f} + 关键词 {s_keyword:.3f} + "
                f"参数 {s_param:.3f} + 类别 {s_category:.3f} "
                f"→ 综合 {combined:.3f}"
            ),
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
