# -*- coding: utf-8 -*-
"""Text preprocessing: synonym normalization and tokenization.

Turns free-form (often colloquial) Chinese engineering text into a
normalized token sequence suitable for TF-IDF vectorization.
"""

import re

# ── Optional jieba tokenizer with a regex fallback ──
try:
    import jieba
    # Register engineering-domain terms so jieba does not over-split them.
    _DOMAIN_WORDS = [
        '实心砖墙', '加气混凝土砌块', '挤塑聚苯板', '构造柱', '圈梁', '预制空心板',
        '混合砂浆', '水泥砂浆', '聚合物砂浆', '真石漆', '乳胶漆', '断桥铝合金',
        '中空玻璃', '热熔法', '无障碍扶手', '无障碍坡道', '电伴热', '融雪系统',
        '钢结构井道', '玻璃幕墙', '碳纤维加固', '透水砖', '水稳基层', '沥青面层',
        'SBS改性沥青', '渗透结晶', 'NB-IoT', '综合管沟', '独立基础', '雨落管',
        '散水', '女儿墙', '门禁', '弱电管沟', '日间照料', '适老化',
    ]
    for _w in _DOMAIN_WORDS:
        jieba.add_word(_w)
    HAS_JIEBA = True
except ImportError:  # pragma: no cover - depends on environment
    HAS_JIEBA = False


# Colloquial / shorthand expression → standard term mapping.
SYNONYM_MAP = {
    '砖墙': '实心砖墙', '老楼': '', '一楼': '首层', '老砖': 'MU10实心砖',
    '保温板': '挤塑聚苯板', '苯板': '挤塑聚苯板', '砂浆': '水泥砂浆',
    '钢筋': 'HRB400钢筋', '扶手': '不锈钢扶手', '坡道': '无障碍坡道',
    '电梯': '钢结构电梯井道', '涂料': '外墙涂料', '刷墙': '乳胶漆',
    '贴砖': '瓷砖铺贴', '防水': 'SBS改性沥青防水',
    '5公分': '50mm', '3公分': '30mm', '10公分': '100mm',
    '老楼砖墙': '实心砖墙', '加个坡道': '无障碍坡道',
    '让轮椅能下去': '无障碍坡道', '翻新': '改造',
}


def normalize_query(text):
    """Normalize colloquial descriptions into standard engineering terms."""
    result = text
    for col, std in SYNONYM_MAP.items():
        result = result.replace(col, std)
    # Unify thickness notation: "370厚" → "370mm"
    result = re.sub(r'(\d+)\s*厚(?!度)', r'\1mm', result)
    # Unify Chinese numerals for floor/building counts.
    num_map = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
               '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
    for cn, n in num_map.items():
        result = result.replace(cn + '层', n + '层').replace(cn + '栋', n + '栋')
    return result


def tokenize(text):
    """Tokenize text into a list of tokens (jieba first, regex fallback)."""
    text = text.lower()
    if HAS_JIEBA:
        tokens = [t for t in jieba.cut(text) if len(t.strip()) > 1]
    else:
        tokens = re.findall(r'[一-鿿]{2,}|[a-zA-Z]{2,}|\d+\.?\d*', text)
        tokens = [t for t in tokens if len(t) > 1]
    # Additionally extract numeric value + unit pairs (e.g. "120mm").
    dims = re.findall(r'(\d+)\s*(mm|m|m2|m3|层|部|处|套|t|吨)', text)
    for d, u in dims:
        tokens.append(f'{d}{u}')
    return tokens
