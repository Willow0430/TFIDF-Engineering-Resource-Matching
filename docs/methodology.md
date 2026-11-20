# Methodology & Technical Route

## 1. Research problem and context

This project originated in an engineering-cost / BIM scenario: mapping
component descriptions from a building model (or a renovation checklist) to
pricing-quota work items. The task is a **text ranking** problem over a fixed
candidate library — a constrained information-retrieval setting rather than
open-domain question answering.

## 2. Why this approach

Three candidate approaches were considered:

| Approach                | Pros                                | Cons                                          |
|-------------------------|-------------------------------------|-----------------------------------------------|
| Rule / keyword matching | trivial, fast                       | brittle; misses synonyms & dimensions         |
| **TF-IDF + fusion**     | interpretable, no training, robust  | bag-of-words; weak on unseen paraphrases      |
| Transformer (BERT, …)   | strong semantics                    | heavy, needs data, GPU, harder to interpret   |

TF-IDF was chosen as the **pragmatic baseline**: the domain text is short and
term-dense, so lexical overlap is a strong signal; and adding a synonym map +
dimension matching recovers most of what a bag-of-words model loses. It runs
on a laptop CPU in milliseconds per query, which matters for batch processing
thousands of BIM components.

## 3. Technical route

```
① Normalize ── ② Tokenize ── ③ Vectorize ── ④ Score & Rank ── ⑤ Output
```

1. **Normalize** — map colloquial/shorthand to standard terms and unify
   numeric notation, so the tokenizer sees a canonical form.
2. **Tokenize** — jieba segmentation with domain terms registered; regex
   fallback guarantees the module runs without jieba.
3. **Vectorize** — compute a smoothed IDF table once over the corpus, then
   weight each query/resource by TF·IDF.
4. **Score & rank** — fuse cosine similarity with keyword and dimension
   heuristics, discard weak candidates, sort by combined score.
5. **Output** — return ranked entries with confidence and reliability labels;
   optionally feed into a change-cost predictor.

## 4. Module relationships

```
preprocessing.py ◄──────────── similarity.py
      │  ▲                          │
      │  └──────────────┐           │
      ▼                 │           ▼
quota_db.py ──► matching.py ──► evaluation.py
      ▲                 │
      │                 └──────► web.py
      └──────► scripts/export_data.py
```

- `quota_db.py` supplies the corpus; `matching.py` builds the IDF table from
  it and exposes `match_quota` / `predict_change`.
- `similarity.py` depends on `preprocessing.py` (for `tokenize` in the
  keyword heuristic).
- `evaluation.py` and `web.py` are thin consumers of `matching.py`.
- `scripts/export_data.py` regenerates the CSV artifacts from the same
  source of truth.

## 5. Design decisions

- **Weights (0.65 / 0.20 / 0.15)** — cosine dominates because it is the most
  reliable signal; keyword and dimension boosts break ties and fix dimension
  sensitivity without overpowering the lexical core.
- **Threshold `0.03`** — prunes obviously irrelevant candidates, keeping the
  top-k list clean without dropping true near-misses.
- **Two reliability cutoffs (`0.25` / `0.12`)** — coarse human-facing labels
  rather than a calibrated probability.
- **Hardcoded library** — chosen for out-of-the-box reproducibility; loading
  from CSV is listed as future work.

## 6. Evaluation methodology

- **Data**: 30 curated queries — 20 standard descriptions plus 10 colloquial
  / shorthand cases — spanning all 21 specialties.
- **Metric**: top-1 category accuracy, plus confidence and latency.
- **Procedure**: run the suite end-to-end, record per-case verdicts, report
  accuracy by case type. Full numbers in `results/experiment_report.md`.

## 7. Future roadmap

- Replace the bag-of-words core with sentence embeddings for paraphrases.
- Load the library from CSV; support user-defined corpora.
- Add compound pricing (wall = masonry + insulation + finishing).
- Benchmark on a larger labeled corpus with cross-validation.
