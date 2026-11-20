# Algorithm Description

This document describes the algorithm **actually implemented** in this
project. TF-IDF and cosine similarity are well-established classical methods —
no claim of originality is made for the core algorithm itself; the project's
contribution is the *engineering pipeline* (normalization + fused scoring)
tailored to short, term-heavy Chinese engineering text.

## 1. Pipeline overview

```
raw description
   │  1. normalize_query(): synonym map + unit/full-width unification
   ▼
normalized text
   │  2. tokenize(): jieba (or regex fallback) + grade/unit-pair extraction
   ▼
token list
   │  3. compute_tfidf_vector(): TF × IDF over the resource corpus
   ▼
query vector
   │  4. score every resource: fused text / keyword / parameter / category
   ▼
ranked top-k with confidence + reliability
```

## 2. Text normalization (`normalize_query`)

Free-form input is rewritten before tokenization:

- **Conservative synonym map** — a small dictionary replaces only genuinely
  equivalent wording, e.g. `一楼` → `首层`, `让轮椅能下去` → `无障碍坡道`,
  `翻新` → `改造`. Material/spec over-generalizations are deliberately NOT
  listed here (that decision is left to the parameter matcher).
- **Full-width → half-width** — ideographic digits/letters and U+3000 space
  are normalized so `５公分` behaves like `5公分`.
- **Thickness / colloquial units** — `(\d+)\s*公分` → `×10mm` (so `5公分` →
  `50mm`), and `(\d+)\s*厚(?!度)` → `\1mm` (so `370厚` → `370mm`).
- **Unit unification** — `㎡`/`m²`/`m2`/`平米` → `平方米`, `m³`/`m3` → `立方米`.
- **Chinese numerals** — `一层` → `1层`, `一栋` → `1栋`, etc.

## 3. Tokenization (`tokenize`)

- If `jieba` is installed, use `jieba.cut`; a list of engineering domain terms
  is registered first so jieba does not over-split compound terms such as
  `加气混凝土砌块`.
- If `jieba` is missing, fall back to a regex tokenizer (CJK runs ≥2, ASCII
  letters, numbers).
- Grade tokens are appended explicitly so they survive over-splitting:
  rebar grade (`hpb300`/`hrb335`/`hrb400`/`hrb500`), concrete grade (`c\d{2}`),
  mortar grade (`m\d+(\.\d+)?`, excluding `m2`/`m3`), and numeric `value+unit`
  pairs (`mm`, `平方米`, `立方米`, `层`, `部`, `处`, `套`, …).

## 4. TF-IDF vectorization

**IDF** (smoothed) is computed once over the whole resource corpus:

```
idf(w) = log((N + 1) / (df(w) + 1)) + 1
```

where `N` is the number of documents (resources) and `df(w)` the number of
documents containing token `w`.

**TF** is term frequency normalized by document length:

```
tf(w) = count(w) / |tokens|
```

The weight vector is the product `tf(w) · idf(w)`; tokens absent from the
corpus receive a default idf of `1` (kept, not dropped).

## 5. Similarity & scoring

**Cosine similarity** over the sparse weight vectors:

```
cosine(a, b) = (Σ a_w · b_w) / (√Σ a_w² · √Σ b_w²)
```

**Four fused signals** per candidate resource:

```
S = 0.40 · S_text + 0.25 · S_keyword + 0.25 · S_param + 0.10 · S_category
```

- `S_text` — TF-IDF cosine similarity in `[0, 1]`.
- `S_keyword` — `keyword_match`: weighted token-overlap ratio in `[0, 1]`;
  strong engineering terms (`构造柱`, `圈梁`, `SBS`, `XPS`, …) weigh double.
- `S_param` — `parameter_match_score` in `[-1, 1]`: compares extracted
  dimensions and strength/material parameters. A **hard conflict** on a
  specification parameter (thickness / cross-section / diameter, or
  concrete / mortar / rebar grade) returns `-0.6` to demote a textually
  similar but incompatible resource; missing specs cost `-0.15`; quantities
  (area / volume / floors / count) use a ratio in `[0, 1]`; material overlap
  is a Jaccard-like ratio.
- `S_category` — `category_match` in `[0, 1]`: specialty-keyword affinity via
  substring containment (`实心砖墙` still matches keyword `砖墙`).

The weights are an **experimental starting point** and are tuned by the
ablation study in `evaluation.py`; they are not claimed to be optimal.

Candidates with `combined ≤ MIN_SCORE (0.05)` are discarded. The remainder are
sorted by descending `combined` and truncated to `top_k`.

**Confidence & reliability** are derived from `combined`:

```
confidence  = min(combined · 100, 99.9)   (percent)
reliability = high   if combined ≥ 0.45
              medium if combined ≥ 0.20
              low    otherwise
```

## 6. Change-cost prediction (`predict_change`)

A separate module maps `(change_type, area, component)` to a cost band. For
each of 24 training samples it blends text similarity with an area-proximity
factor:

```
score = 0.55 · cosine(query, sample_text) + 0.45 · (1 - |area - sample_area| / max(area, sample_area, 1))
```

The top-5 samples vote (weighted by score) on a cost band
(`节约`, `小额<50万`, `中额50-200万`, `大额>200万`); the predicted amount is a
score-weighted average.

## 7. Applicability & limitations

**Suitable for** short, term-dense, dictionary-overlapping text where the
candidate set is a fixed, curated library — exactly the construction
"component → quota" matching scenario.

**Limitations** (inherent to TF-IDF):

- Bag-of-words: word order and syntax are ignored.
- Out-of-vocabulary paraphrases (beyond the synonym map) will not match.
- Term-frequency bias: rare-but-relevant tokens can be diluted by common ones.
- No semantic understanding: synonyms not in the map are treated as distinct.
- The parameter signal's hard conflict penalty can be over-aggressive at the
  current weights; see the ablation results.

For these reasons the project treats TF-IDF as a strong, interpretable
baseline and documents embedding-based models as the natural next step.
