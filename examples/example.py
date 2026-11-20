# -*- coding: utf-8 -*-
"""Minimal usage examples for the TF-IDF engineering resource matcher.

Run from the project root:

    python examples/example.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src import QUOTA_DB, match_quota, normalize_query, predict_change  # noqa: E402


def main():
    print("Resource library: %d entries across %d specialties"
          % (len(QUOTA_DB), len(set(q['category'] for q in QUOTA_DB))))
    print()

    # 1. Standard, well-formed description
    print("=== Example 1: standard description ===")
    for m in match_quota("370mm实心砖墙 M5混合砂浆 砖混住宅", top_k=3):
        q = m["quota"]
        print("  [%s] %s | %s yuan/%s | confidence %.1f%%"
              % (q["id"], q["name"], q["unit_price"], q["unit"], m["confidence"]))

    # 2. Colloquial / shorthand description (auto-normalized)
    print("\n=== Example 2: colloquial description ===")
    raw = "老楼砖墙370厚 抹水泥20 翻新"
    normalized = normalize_query(raw)
    print("  raw:        %s" % raw)
    print("  normalized: %s" % normalized)
    m = match_quota(raw, top_k=1)[0]
    print("  best match: [%s] %s (%.1f%%)"
          % (m["quota"]["id"], m["quota"]["name"], m["confidence"]))

    # 3. Change-cost prediction
    print("\n=== Example 3: change-cost prediction ===")
    p = predict_change("扶手加装", 350, "不锈钢扶手D38")
    print("  %s %s | predicted ~%.0f wan | confidence %.0f%%"
          % (p["risk_tag"], p["predicted_level"],
             p["predicted_amount"], p["confidence"] * 100))


if __name__ == "__main__":
    main()
