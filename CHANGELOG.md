# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and versioning follows
[SemVer](https://semver.org/).

## [3.0.0] - 2026-11-20

### Changed
- **Scoring model**: replaced the three-signal fusion (cosine 0.65 + keyword
  0.20 + dimension 0.15) with four interpretable signals — text similarity
  0.40, keyword overlap 0.25, parameter match 0.25, category affinity 0.10.
  These weights are explicitly an *experimental starting point*, not a claim
  of optimality.
- **Preprocessing**: conservative synonym map (removed over-generalizing
  entries), added stopwords, full-width → half-width conversion, and unit
  unification (㎡/m2/平米 → 平方米).
- **Similarity**: renamed `dimension_match_score`/`keyword_boost` to
  `parameter_match_score`/`keyword_match`; added strength/material extraction
  (concrete/mortar/rebar grade) with a hard conflict penalty for incompatible
  specifications.
- **Evaluation**: split accuracy into *category* vs *resource-id* levels;
  added an independent labeled test set with human-annotated 资源编号
  (flagged best-effort), Top-1/Top-3 accuracy, Precision@k, Recall@k, MRR,
  and an A/B/C/D ablation study (`run_ablation`).

### Fixed
- CJK/ASCII word-boundary bug (`\b` fails between Chinese and grade letters),
  which previously made mortar/concrete grades extract as `None`.
- Full-width digits and colloquial units (`５公分`, `㎡`) now normalize
  correctly.

### Added
- `validate_db` data-integrity check and `DATA_SOURCE` / `LAST_UPDATED`
  provenance fields in `quota_db.py`.
- `weights` override parameter on `match_quota` for ablation experiments.
- Expanded pytest suite (6 test modules) covering normalization, TF-IDF,
  similarity, matching, evaluation metrics, and edge cases.

### Known limitations
- The parameter signal currently *reduces* accuracy on the 30-case set at the
  default weights; tuning on a larger held-out set is still needed.

## [2.0.0] - 2025 (prior release)
- Initial TF-IDF + keyword + dimension fusion with a 202-entry library and a
  Gradio web demo.
