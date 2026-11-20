# -*- coding: utf-8 -*-
"""Export the resource library and evaluation results to CSV.

Run from the project root:

    python scripts/export_data.py

Generates:
    data/quota_database.csv    - full resource library (202 entries)
    data/sample_queries.csv    - the 30 built-in test queries
    results/sample_result.csv  - top-1 match for every test query

CSVs are written with a UTF-8 BOM so they open correctly in Excel.
"""

import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import QUOTA_DB, LABELED_TEST_CASES, match_quota  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
RESULTS_DIR = os.path.join(ROOT, "results")


def _write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print("wrote %s (%d rows)" % (os.path.relpath(path, ROOT), len(rows)))


def export_quota_db():
    rows = [[q["id"], q["name"], q["unit"], q["unit_price"], q["category"], q["desc"]]
            for q in QUOTA_DB]
    _write_csv(os.path.join(DATA_DIR, "quota_database.csv"),
               ["id", "name", "unit", "unit_price", "category", "description"], rows)


def export_sample_queries():
    rows = [[c["query"], c["category"], "|".join(c["ids"]),
             "是" if c["ambiguous"] else "否", c["note"]]
            for c in LABELED_TEST_CASES]
    _write_csv(os.path.join(DATA_DIR, "sample_queries.csv"),
               ["query", "expected_category", "expected_ids", "ambiguous", "note"], rows)


def export_sample_results():
    rows = []
    for c in LABELED_TEST_CASES:
        case_text = c["query"]
        start = time.perf_counter()
        matches = match_quota(case_text, top_k=3)
        elapsed = time.perf_counter() - start
        if matches:
            top = matches[0]
            q = top["quota"]
            predicted_ids = [m["quota"]["id"] for m in matches]
            id_ok = "OK" if any(pid in c["ids"] for pid in predicted_ids) else "XX"
            cat_ok = "OK" if q["category"] == c["category"] else "XX"
            rows.append([case_text, c["category"], q["category"], cat_ok,
                         "|".join(c["ids"]), id_ok, q["id"], q["name"],
                         q["unit"], q["unit_price"], round(top["confidence"], 1),
                         top["reliability"], round(elapsed * 1000, 3), c["note"]])
        else:
            rows.append([case_text, c["category"], "无匹配", "XX",
                         "|".join(c["ids"]), "XX", "", "", "", "", "",
                         "none", round(elapsed * 1000, 3), c["note"]])
    _write_csv(os.path.join(RESULTS_DIR, "sample_result.csv"),
               ["query", "expected_category", "matched_category", "category_verdict",
                "expected_ids", "id_verdict", "matched_id", "matched_name", "unit",
                "unit_price", "confidence(%)", "reliability", "time_ms", "note"], rows)


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    export_quota_db()
    export_sample_queries()
    export_sample_results()
