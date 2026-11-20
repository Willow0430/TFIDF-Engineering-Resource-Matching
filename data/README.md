# Data

## `quota_database.csv`

The built-in engineering resource library — **202 entries** across **21
specialties** (masonry, concrete, rebar, insulation, waterproofing, finishing,
doors/windows, steel, MEP, municipal, landscaping, accessibility, demolition,
measures, smart systems).

| Column         | Meaning                                          |
|----------------|--------------------------------------------------|
| `id`           | Resource / work-item code (e.g. `4-1-8`)         |
| `name`         | Normalized name (used for matching)              |
| `unit`         | Measurement unit (m3, m2, m, t, 套, ...)         |
| `unit_price`   | Unit price (yuan)                                |
| `category`     | Specialty category                               |
| `description`  | Free-text description (used for matching)        |

**Source / provenance:** curated from the publicly published *Liaoning Province
construction pricing quota (2024 edition)* and *Shenyang material price
information*. The underlying standards remain the property of their publishers
— verify their terms of use before redistributing. The Python source of truth
is `src/quota_db.py`; this CSV is a generated export
(see `scripts/export_data.py`).

## `sample_queries.csv`

The 30 built-in test queries (20 standard + 10 colloquial).

| Column               | Meaning                          |
|----------------------|----------------------------------|
| `query`              | Input text                       |
| `expected_category`  | Ground-truth specialty           |
| `note`               | Test label (标准 / 口语)         |

## Encoding

All CSVs are written as UTF-8 with a BOM (`utf-8-sig`) so they open correctly
in Microsoft Excel. Regenerate them at any time with:

```bash
python scripts/export_data.py
```
