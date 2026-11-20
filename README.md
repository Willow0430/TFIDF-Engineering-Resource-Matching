# TFIDF-Engineering-Resource-Matching

TF-IDF based **engineering resource semantic matching**. Turn free-form
(often colloquial) Chinese engineering text into TF-IDF vectors and rank
candidate resources via a fused cosine / keyword / dimension score.

> **English** | [中文文档](README_CN.md)

---

## Project Overview

In engineering cost estimation and BIM-based project management, a recurring
bottleneck is mapping a natural-language description of a component (a wall,
a column, a handrail, a section of road, …) to a structured resource entry
with a code and a unit price. This is traditionally done by hand — an expert
flips through a printed pricing quota, reads a description, and picks the
closest work item.

This project replaces that manual lookup with a lightweight, interpretable NLP
pipeline: normalize the text, tokenize it, weight it with TF-IDF, and rank
candidate resources by a fused similarity score. It ships with a 202-entry
example library spanning 21 engineering specialties, so it runs out of the box.

## Research Background

- **Domain problem.** Construction "quota" matching (定额匹配) is a
  low-level, high-frequency, expert-dependent task in engineering cost
  management. Manual matching is slow (2–3 minutes per item) and inconsistent
  between different estimators.
- **Why TF-IDF.** Classical TF-IDF + cosine similarity is interpretable, has
  near-zero training cost, and — with domain synonym normalization — handles
  the short, term-heavy descriptions typical of engineering text well. It is a
  pragmatic baseline before considering heavier embedding models (e.g. BERT).

## Problem Statement

> Given a natural-language engineering resource description (possibly
> colloquial or shorthand), find the most relevant entry in a structured
> resource library, and report a ranked list with confidence scores.

Concretely, the matcher must handle:

- Standard descriptions: `370mm实心砖墙 M5混合砂浆 砖混住宅`
- Colloquial / shorthand input: `老楼砖墙370厚 抹水泥20 翻新`
- Dimension-sensitive queries: thickness, cross-section, counts, floors.

## Main Features

- **Text normalization** — colloquial → standard term mapping, thickness
  notation unification (`370厚` → `370mm`), Chinese numeral normalization.
- **Robust tokenization** — jieba first, with a built-in regex fallback when
  jieba is not installed.
- **TF-IDF vectorization** — smoothed IDF weighting over the resource corpus.
- **Fused scoring** — four interpretable signals: text similarity (0.40),
  keyword overlap (0.25), parameter match (0.25) and category affinity (0.10).
  These weights are an experimental starting point, tuned via an ablation study
  (`run_ablation`), and are not claimed to be optimal.
- **Confidence & reliability** — every match reports a percentage confidence
  and a high / medium / low reliability label.
- **Change-cost prediction** — a bonus module that maps a change type + area
  to a predicted cost band via TF-IDF similarity.
- **Optional Gradio web demo** — interactive browser UI.

## Technical Framework

```
description ─▶ normalize ─▶ tokenize ─▶ TF-IDF vector
                                              │
                     text sim (0.40)  ────────┤
                     keyword (0.25)  ─────────┼──▶ combined score ─▶ rank ─▶ top-k
                     parameter (0.25) ────────┤
                     category (0.10) ─────────┘
```

| Module              | Responsibility                                      |
|---------------------|-----------------------------------------------------|
| `preprocessing.py`  | normalization, tokenization                         |
| `tfidf.py`          | IDF + TF-IDF vector computation                     |
| `similarity.py`     | cosine similarity, parameter & keyword heuristics   |
| `quota_db.py`       | the 202-entry resource library                      |
| `matching.py`       | `match_quota` and `predict_change`                  |
| `evaluation.py`     | labeled test set, metrics, ablation study           |
| `web.py`            | Gradio web demo                                     |

## Project Structure

```
TFIDF-Engineering-Resource-Matching/
├── README.md               # this file
├── README_CN.md            # Chinese documentation
├── LICENSE                 # MIT
├── requirements.txt
├── main.py                 # CLI entry point
├── pytest.ini
├── src/                    # the library
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── tfidf.py
│   ├── similarity.py
│   ├── quota_db.py
│   ├── matching.py
│   ├── evaluation.py
│   ├── web.py
│   └── cli.py
├── data/
│   ├── quota_database.csv  # exported resource library
│   ├── sample_queries.csv  # the 30 test queries
│   └── README.md
├── tests/                  # pytest suite
├── examples/               # usage examples
├── docs/                   # algorithm / methodology / user guide
├── results/                # sample results + experiment report
├── images/                 # generated diagrams
└── scripts/                # data/chart export scripts
```

## Installation

Requires Python 3.8+.

```bash
git clone https://github.com/Willow0430/TFIDF-Engineering-Resource-Matching.git
cd TFIDF-Engineering-Resource-Matching
pip install -r requirements.txt
```

`jieba` is the only core dependency and the matcher degrades gracefully to a
regex tokenizer if it is missing. `gradio` and `matplotlib` are optional.

## Quick Start

```bash
# run the built-in evaluation suite (30 cases)
python main.py --report

# interactive command-line demo
python main.py --demo

# launch the browser web demo
python main.py --web
```

## Usage Examples

```python
from src import match_quota, predict_change, normalize_query

# Standard description
for m in match_quota("370mm实心砖墙 M5混合砂浆 砖混住宅", top_k=3):
    print(m["quota"]["id"], m["quota"]["name"], f"{m['confidence']:.1f}%")

# Colloquial description (auto-normalized)
print(normalize_query("老楼砖墙370厚 抹水泥20 翻新"))

# Change-cost prediction
print(predict_change("扶手加装", 350, "不锈钢扶手D38"))
```

See `examples/example.py` for a runnable version.

## Sample Results

The 30 built-in cases (20 standard + 10 colloquial) are reported at **two
levels**, which must not be conflated:

| Metric                                              | Result          |
|-----------------------------------------------------|-----------------|
| Category accuracy, top-1 (类别匹配率)                | **29/30 = 96.7%** |
| Resource-id accuracy, top-1 (资源编号匹配率, best-effort) | 29/30 = 96.7%   |
| Resource-id MRR@3                                    | 0.967           |
| Average confidence                                   | ~71%            |
| Average latency                                      | ~32 ms / case   |

The category figure is what the original "96.7%" actually measured. The
resource-id figure depends on a **best-effort** annotation of the correct
资源编号 that still needs confirmation by a domain expert — it is not yet an
authoritative claim.

The single top-1 miss is `门口路面铺沥青 小区车行道 底下水稳20公分`, which
matched a masonry-block wall instead of the asphalt-road resource. An ablation
study (pure TF-IDF vs +keyword vs +parameter vs full fusion) shows the parameter
signal currently *reduces* accuracy at the default weights (90.0% vs 100.0% for
text+keyword on this small set) — so the fusion weights are experimental and
must be tuned on a held-out set. Full per-case detail is in `results/` and can
be regenerated with `python main.py --report` / `python main.py --ablation`.

## Limitations

- **Bag-of-words model.** TF-IDF ignores word order; long or ambiguous
  descriptions can degrade.
- **Domain data is curated.** The shipped library is a 202-entry subset, not
  the full provincial quota. Prices are indicative.
- **Colloquial coverage is incomplete.** The synonym dictionary handles common
  cases but not arbitrary dialect or abbreviations.
- **No true semantic understanding.** Paraphrases beyond the synonym map will
  not match; a transformer embedding model is the natural next step.

## Future Development

See `docs/methodology.md` and the roadmap items below:

- Upgrade the matching core to a BERT / sentence-embedding model for better
  colloquial coverage.
- Load the resource library from a user-supplied CSV instead of a hardcoded
  module.
- Add compound-pricing logic (e.g. wall = masonry + insulation + finishing).
- Benchmark against a larger, labeled corpus.

## License

MIT — see [LICENSE](LICENSE). The bundled resource library is a curated subset
derived from the publicly published *Liaoning Province construction pricing
quota (2024 edition)* and *Shenyang material price information*; verify the
source terms of use before redistributing the data.
