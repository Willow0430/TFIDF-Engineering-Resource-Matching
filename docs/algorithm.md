# Algorithm Description

This document describes the algorithm **actually implemented** in this
project. TF-IDF and cosine similarity are well-established classical methods —
no claim of originality is made for the core algorithm itself; the project's
contribution is the *engineering pipeline* (normalization + fusion scoring)
tailored to short, term-heavy Chinese engineering text.

## 1. Pipeline overview

```
raw description
   │  1. normalize_query(): synonym map + notation unification
   ▼
normalized text
   │  2. tokenize(): jieba (or regex fallback) + unit-pair extraction
   ▼
token list
   │  3. compute_tfidf_vector(): TF × IDF over the resource corpus
   ▼
query vector
   │  4. score every resource: 0.65·cosine + 0.20·keyword + 0.15·dimension
   ▼
ranked top-k with confidence + reliability
```

## 2. Text normalization (`normalize_query`)

Free-form input is rewritten before tokenization:

- **Synonym mapping** — a small dictionary replaces colloquial / shorthand
  terms with standard ones, e.g. `保温板` → `挤塑聚苯板`, `苯板` →
  `挤塑聚苯板`, `一楼` → `首层`, `5公分` → `50mm`.
- **Thickness notation** — `(\d+)\s*厚(?!度)` → `\1mm`, so `370厚` becomes
  `370mm` while `厚度` is left untouched.
- **Chinese numerals** — `一层` → `1层`, `一栋` → `1栋`, etc.

## 3. Tokenization (`tokenize`)

- If `jieba` is installed, use `jieba.cut`; a list of ~40 engineering domain
  terms is registered first so jieba does not over-split compound terms such
  as `加气混凝土砌块`.
- If `jieba` is missing, fall back to a regex tokenizer that captures runs of
  CJK characters (≥2), ASCII letters (≥2), or numbers.
- In both cases, numeric `value + unit` pairs (`mm`, `m`, `m2`, `m3`, `层`,
  `部`, `处`, `套`, `t`, `吨`) are appended as additional tokens so dimensions
  participate in matching.

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
corpus receive a default idf of `1`.

## 5. Similarity & scoring

**Cosine similarity** over the sparse weight vectors:

```
cosine(a, b) = (Σ a_w · b_w) / (√Σ a_w² · √Σ b_w²)
```

**Fused score** per candidate resource:

```
combined = 0.65 · cosine(query, resource)
         + 0.20 · keyword_boost(query, resource)
         + 0.15 · dimension_match(query, resource)
```

- `keyword_boost` (range `[0, 0.2]`): counts token overlap; a set of strong
  engineering terms (`构造柱`, `圈梁`, `SBS`, `XPS`, …) is weighted double.
- `dimension_match` (range `[0, 0.3]`): compares extracted numeric dimensions
  (thickness, cross-section, area, floors, count). For each shared dimension,
  it adds `0.06 · min/max`; the total is capped at 0.3.

Candidates with `combined ≤ 0.03` are discarded. The remainder are sorted by
descending `combined` and truncated to `top_k`.

**Confidence & reliability** are derived from `combined`:

```
confidence  = min(combined · 100, 99.9)   (percent)
reliability = high   if combined > 0.25
              medium if combined > 0.12
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

For these reasons the project treats TF-IDF as a strong, interpretable
baseline and documents embedding-based models as the natural next step.
