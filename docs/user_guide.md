# User Guide

A step-by-step guide for users who have never used this project.

## 1. Prerequisites

- **Python 3.8 or newer** (developed and tested on 3.12).
- A terminal (PowerShell on Windows, or bash on macOS/Linux).

Verify Python is available:

```bash
python --version
```

## 2. Get the code

```bash
git clone https://github.com/Willow0430/TFIDF-Engineering-Resource-Matching.git
cd TFIDF-Engineering-Resource-Matching
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

- `jieba` (required for best Chinese tokenization). If you skip it, the
  matcher falls back to a built-in regex tokenizer and still runs.
- `gradio` (optional — web demo), `matplotlib` (optional — charts),
  `pytest` (optional — tests).

## 4. Run it

```bash
# evaluation suite (30 cases) — the default
python main.py --report

# interactive demo
python main.py --demo

# browser web demo (needs gradio)
python main.py --web

# run tests then demo
python main.py --all
```

When `--web` is used, open the printed URL (default `http://127.0.0.1:7860`)
in a browser.

## 5. Use it as a library

```python
from src import match_quota, predict_change, normalize_query

# Top-3 matches for a description
for m in match_quota("370mm实心砖墙 M5混合砂浆 砖混住宅", top_k=3):
    q = m["quota"]
    print(q["id"], q["name"], f"{m['confidence']:.1f}%")

# Normalize colloquial input
print(normalize_query("老楼砖墙370厚 抹水泥20"))

# Change-cost prediction
print(predict_change("扶手加装", 350, "不锈钢扶手D38"))
```

A runnable script is in `examples/example.py`.

## 6. Understand the output

Each match is a dict:

| Field          | Meaning                                              |
|----------------|------------------------------------------------------|
| `quota`        | the matched resource (id, name, unit, unit_price, category, desc) |
| `s_text`       | TF-IDF cosine similarity (weight 0.40)               |
| `s_keyword`    | weighted keyword-overlap ratio (weight 0.25)         |
| `s_param`      | parameter-match score in [-1,1] (weight 0.25)        |
| `s_category`   | category-affinity score (weight 0.10)                |
| `combined`     | fused score                                          |
| `confidence`   | combined × 100, capped at 99.9                       |
| `reliability`  | `high` / `medium` / `low`                            |

## 7. Add your own resource library

Edit `src/quota_db.py` and follow the `add(id, name, unit, price, category,
desc)` pattern, then re-export the CSV:

```bash
python scripts/export_data.py
```

## 8. Troubleshooting

**Chinese output looks garbled in the console.**

On Windows, the CLI entry (`src/cli.py`) already forces UTF-8 stdout. If you
still see mojibake, run:

```powershell
$env:PYTHONIOENCODING = "utf-8"; python main.py --report
```

**"No module named jieba".**

```bash
pip install jieba
```

Or simply ignore it — the regex fallback still works (accuracy may be
slightly lower for some compound terms).

**`--web` says Gradio is not installed.**

```bash
pip install gradio
```

## 9. Run the tests

```bash
python -m pytest
```

Expect `21 passed`.
