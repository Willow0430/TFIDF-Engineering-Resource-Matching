# -*- coding: utf-8 -*-
"""Text preprocessing: normalization and tokenization for engineering text.

Responsibilities:
- Normalize free-form Chinese engineering descriptions (units, full/half-width,
  whitespace) WITHOUT changing the underlying engineering meaning.
- Tokenize into TF-IDF-ready tokens, preserving professional parameters
  (rebar grade, concrete strength, mortar grade, material model, dimensions).
"""

import re

# ── Optional jieba tokenizer with a regex fallback ──
try:
    import jieba
    _DOMAIN_WORDS = [
        '实心砖墙', '加气混凝土砌块', '陶粒混凝土砌块', '多孔砖墙', '空心砖墙',
        '挤塑聚苯板', '构造柱', '圈梁', '预制空心板', '独立基础', '条形基础',
        '混合砂浆', '水泥砂浆', '聚合物砂浆', '真石漆', '乳胶漆', '断桥铝合金',
        '中空玻璃', '热熔法', '无障碍扶手', '无障碍坡道', '电伴热', '融雪系统',
        '钢结构井道', '玻璃幕墙', '碳纤维加固', '透水砖', '水稳基层', '沥青面层',
        'SBS改性沥青', '渗透结晶', 'NB-IoT', '综合管沟', '雨落管', '散水',
        '女儿墙', '门禁', '弱电管沟', '日间照料', '适老化', '植筋', '钢筋制安',
        '钢筋机械连接', '防水卷材', '防火门', '塑钢窗', '平开窗', '踢脚线',
        '防水涂料', '防水砂浆', '保温砂浆', '抗裂砂浆', '抹灰', '找平层',
        '界面剂', '防水层', '保温层', '隔热层', '隔声层', '吊顶', '龙骨',
        '矿棉板', '硅酸钙板', '防火涂料', '面砖', '花岗岩', '大理石板',
        '成品保护', '安全文明', '脚手架', '垂直运输', '拆除', '清运',
        '混凝土柱', '混凝土梁', '混凝土板', '混凝土墙', '混凝土基础',
    ]
    for _w in _DOMAIN_WORDS:
        jieba.add_word(_w)
    HAS_JIEBA = True
except ImportError:  # pragma: no cover - depends on environment
    HAS_JIEBA = False


# Conservative colloquial -> standard synonyms only. Entries must NOT
# over-generalize a category, material or specification (that decision is left
# to the parameter matcher); they only normalize genuinely equivalent wording.
SYNONYM_MAP = {
    '一楼': '首层',
    '让轮椅能下去': '无障碍坡道',
    '翻新': '改造',
}

# Stopwords: high-frequency function words with no engineering meaning.
# Deliberately minimal — single-char particles are already dropped by the
# length filter, and no domain term is ever listed here.
STOPWORDS = {
    '进行', '以及', '包括', '用于', '采用', '其中', '相应', '相关',
}

# Full-width ASCII (U+FF01..U+FF5E) and ideographic space -> half-width.
_FW_TRANS = str.maketrans(
    {i + 0xFEE0: i for i in range(0x21, 0x7F)} | {0x3000: 0x20}
)

# Unify area / volume unit spellings to the canonical Chinese form.
_AREA_UNITS = ['㎡', 'm²', 'm2', '平米', '平方米']
_VOLUME_UNITS = ['m³', 'm3', '立方米']


def _halfwidth(text):
    return text.translate(_FW_TRANS)


def _unify_units(text):
    # 平方米 (㎡ / m² / m2 / 平米) -> 平方米
    text = re.sub(r'㎡|m²', '平方米', text)
    text = re.sub(r'(?<![a-zA-Z])m2(?![a-zA-Z])', '平方米', text)
    text = text.replace('平米', '平方米')
    # 立方米 (m³ / m3) -> 立方米
    text = re.sub(r'm³', '立方米', text)
    text = re.sub(r'(?<![a-zA-Z])m3(?![a-zA-Z])', '立方米', text)
    return text


def normalize_query(text):
    """Normalize a free-form description into standard engineering wording.

    Returns ``""`` for empty / non-string input. Does not drop professional
    parameters (rebar grade, concrete strength, material model, dimensions).
    """
    if not isinstance(text, str):
        return ""
    text = text.strip()
    if not text:
        return ""

    text = _halfwidth(text)

    # Colloquial shorthand synonyms (longest-first not needed; phrases are distinct).
    for col, std in SYNONYM_MAP.items():
        text = text.replace(col, std)

    # Thickness shorthand: "370厚" -> "370mm", "5公分" (5cm) -> "50mm".
    text = re.sub(r'(\d+(?:\.\d+)?)\s*公分', lambda m: f"{float(m.group(1)) * 10:g}mm", text)
    text = re.sub(r'(\d+(?:\.\d+)?)\s*厚(?!度)', r'\1mm', text)

    text = _unify_units(text)

    # Chinese numerals for floor / building counts.
    num_map = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
               '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
    for cn, n in num_map.items():
        text = text.replace(cn + '层', n + '层').replace(cn + '栋', n + '栋')

    # Collapse stray whitespace.
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text):
    """Tokenize text into a token list (jieba first, regex fallback).

    Professional parameters are appended as explicit tokens so they survive
    tokenizer over-splitting (e.g. ``HRB400``, ``C25``, ``M7.5``, ``370mm``).
    """
    if not isinstance(text, str):
        return []
    text = text.strip().lower()
    if not text:
        return []

    if HAS_JIEBA:
        tokens = [t for t in jieba.cut(text) if len(t.strip()) > 1 and t.strip() not in STOPWORDS]
    else:
        tokens = re.findall(r'[一-鿿]{2,}|[a-z][a-z0-9.+\-]*|\d+(?:\.\d+)?', text)
        tokens = [t for t in tokens if len(t) > 1 and t not in STOPWORDS]

    # Rebar grade, concrete strength, mortar grade (text is already lowercased).
    extra = re.findall(r'(?<![a-z0-9])(?:hpb300|hrb335|hrb400|hrb500)(?![a-z0-9])', text)
    extra += re.findall(r'(?<![a-z0-9])c\d{2}(?![a-z0-9])', text)
    _mortar = re.findall(r'(?<![a-z0-9])m\d+(?:\.\d+)?(?![a-z0-9])', text)
    extra += [x for x in _mortar if x not in ('m2', 'm3')]
    # Numeric value + unit pairs (dimensions / quantities).
    extra += [
        f"{m[0]}{m[1]}"
        for m in re.findall(
            r'(\d+(?:\.\d+)?)\s*(mm|平方米|立方米|m|t|吨|层|部|处|套|根|道|个|座|樘)',
            text,
        )
    ]

    # Deduplicate, preserving order.
    seen = set()
    out = []
    for t in tokens + extra:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out
