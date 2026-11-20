# Experiment Report

This report records the **actual, reproducible** evaluation of the matcher on
the shipped 30-case suite. No results are fabricated; every number below was
obtained by running `python main.py --report` on the environment in §2.

## 1. Test data

| Item               | Value                                  |
|--------------------|----------------------------------------|
| Resource library   | 202 entries, 21 specialties            |
| Test cases         | 30 (20 standard + 10 colloquial)       |
| Ground truth       | expected specialty per query (curated) |
| Data files         | `data/sample_queries.csv`, `results/sample_result.csv` |

The 10 "colloquial" cases are deliberately harder: shorthand, dialect and
mixed descriptions such as `老楼砖墙370厚 抹水泥20 翻新`.

## 2. Test environment

| Item        | Value                              |
|-------------|------------------------------------|
| OS          | Windows 11 (PowerShell)            |
| Python      | 3.12.10                            |
| jieba       | 0.42.1                             |
| pytest      | 9.2.0                              |
| Hardware    | laptop, single CPU                 |

## 3. Test method

1. Load the 30 cases from `src/evaluation.py`.
2. For each case: normalize → tokenize → `match_quota(top_k=3)`.
3. Compare the top-1 matched `category` against the expected category.
4. Record verdict (`correct`), confidence and latency per case.
5. Report top-1 accuracy overall and split by standard / colloquial.

The suite is also encoded as a regression test in
`tests/test_matching.py::test_full_evaluation_accuracy`.

## 4. Results

| Metric                    | Result           |
|---------------------------|------------------|
| Overall accuracy (top-1)  | **29 / 30 = 96.7%** |
| Standard cases (top-1)    | 20 / 20 = 100.0% |
| Colloquial cases (top-1)  | 9 / 10 = 90.0%   |
| Average confidence        | 47.2%            |
| Average latency           | ~26 ms / case    |

### 4.1 The single failure

| Field        | Value                                                        |
|--------------|--------------------------------------------------------------|
| Input        | `一楼单元门口加个坡道让轮椅能下去 要有扶手`                    |
| Expected     | 适老化专项 (accessibility)                                    |
| Matched      | 门窗工程 (doors/windows), confidence 26.7%                    |
| Root cause   | After normalization the text becomes `首层单元门口无障碍坡道… 要有不锈钢扶手`. The dominant overlapping tokens (单元/门口) pull toward door-related items; the phrase `让轮椅能下去` is dropped to an empty synonym, weakening the ramp signal. |

This is the known weakness of a bag-of-words model on long colloquial
sentences, and it is the primary motivation for the roadmap's embedding-model
upgrade.

### 4.2 Per-case detail

The complete 30-row table is in `results/sample_result.csv`. A sample:

```
query                              expected      matched       verdict  conf
370mm实心砖墙 ... 砖混住宅           砌筑工程      砌筑工程      OK       51.5%
C25现浇混凝土构造柱 240x240 ...      混凝土工程    混凝土工程    OK       54.7%
一楼单元门口加个坡道...              适老化专项    门窗工程      XX       26.7%
```

## 5. Result analysis

- **Standard cases are effectively solved** (100%). The lexicon, domain-word
  registration and dimension matching cover the well-formed descriptions.
- **Colloquial cases are strong but not perfect** (90%). Normalization handles
  common shorthand (`370厚`, `5公分`, `老楼`) but not arbitrary paraphrases.
- **Confidence is conservative** (mean 47.2%): because the score is a fused
  linear combination and not a calibrated probability, it should be read as a
  relative ranking signal, not an absolute certainty.

## 6. Comparison with the earlier version

The original competition report (`附录C AI定额匹配测试报告.txt`) documented an
**earlier 30-entry library** with 76.9% accuracy. The current version expands
the library to 202 entries and adds dimension matching and a stronger synonym
map, raising measured accuracy to 96.7%. Some in-code display strings in the
legacy single-file version still carried stale figures (e.g. "86.7%"); the
refactored modules and this report use the values measured above.

## 7. Algorithm limitations

- Bag-of-words: word order and syntax are ignored.
- Out-of-vocabulary paraphrases (beyond the synonym map) do not match.
- The curated 202-entry library is not the full provincial quota; prices are
  indicative.
- Confidence is a ranking score, not a calibrated probability.

## 8. Conclusion

The TF-IDF + fusion pipeline achieves 96.7% top-1 accuracy on the shipped
30-case suite at ~26 ms/case on a laptop CPU, with a single, well-understood
colloquial failure. It is a solid, reproducible baseline for engineering
resource matching.
