# -*- coding: utf-8 -*-
"""Evaluation suite: independent labeled test set, metrics, and ablation study.

Two accuracy notions are reported **separately** and must not be conflated:

- **类别匹配率 (category accuracy)** — whether the top prediction's specialty
  matches the expected specialty. This is well-defined and is what the original
  "96.7%" figure actually measured.
- **资源编号匹配率 (resource-id accuracy)** — whether the top-k predictions
  include the *specific* resource by 编号 (资源编号). This requires human
  annotation; the labels below are **best-effort** and flagged ``verified=False``
  pending confirmation by a domain expert.

Every case keeps its expected specialty and its annotated resource id(s). No
failure case is removed to inflate accuracy.
"""

import csv
import os
import time

from .matching import match_quota, QUOTA_DB
from .preprocessing import normalize_query


# ── Independent labeled test set ────────────────────────────────────────────
# ``ids`` lists every resource 编号 that constitutes a correct answer for the
# query. When a query legitimately maps to several resources (``ambiguous`` is
# True), all listed ids are accepted. ``verified=False`` marks the label as a
# best-effort annotation awaiting human confirmation.
LABELED_TEST_CASES = [
    # ── 标准构件描述 ──
    {'query': '沈阳7层砖混住宅 370mm厚实心砖外墙 MU10红砖 M5混合砂浆',
     'category': '砌筑工程', 'ids': ['4-1-8'], 'note': '标准-370外墙',
     'ambiguous': False, 'verified': False},
    {'query': 'C25现浇混凝土构造柱 240x240 7度抗震设防 每层48根共336根',
     'category': '混凝土工程', 'ids': ['7-1-8'], 'note': '标准-构造柱',
     'ambiguous': False, 'verified': False},
    {'query': 'C25现浇混凝土圈梁 240x180 每层层顶通长布置 配4Φ12主筋',
     'category': '混凝土工程', 'ids': ['7-2-12', '7-6-2'], 'note': '标准-圈梁',
     'ambiguous': True, 'verified': False},
    {'query': '外墙30mm厚XPS挤塑聚苯板保温 聚合物砂浆 耐碱网格布',
     'category': '保温工程', 'ids': ['10-1-34'], 'note': '标准-外墙保温',
     'ambiguous': False, 'verified': False},
    {'query': '屋面SBS改性沥青防水卷材 4mm厚 II型 热熔法施工',
     'category': '防水工程', 'ids': ['9-2-22'], 'note': '标准-屋面防水',
     'ambiguous': False, 'verified': False},
    {'query': '不锈钢无障碍扶手 D38/D50 楼梯间双侧布置 含L型支架固定',
     'category': '适老化专项', 'ids': ['17-2-5'], 'note': '标准-扶手',
     'ambiguous': False, 'verified': False},
    {'query': '钢结构电梯井道 Q235B 含玻璃幕墙围护 6层站 载重630kg',
     'category': '钢结构工程', 'ids': ['5-3-12'], 'note': '标准-电梯井道',
     'ambiguous': False, 'verified': False},
    {'query': '断桥铝合金平开窗 70系列 三玻两腔 5+12A+5+12A+5 沈阳严寒',
     'category': '门窗工程', 'ids': ['16-1-8'], 'note': '标准-断桥铝窗',
     'ambiguous': False, 'verified': False},
    {'query': '内墙20mm水泥砂浆抹灰 1:3水泥砂浆 基层找平',
     'category': '抹灰工程', 'ids': ['12-1-15'], 'note': '标准-内墙抹灰',
     'ambiguous': False, 'verified': False},
    {'query': '真石漆外墙涂料 批刮型 底漆+中涂+面涂三遍',
     'category': '涂料工程', 'ids': ['15-3-8'], 'note': '标准-真石漆',
     'ambiguous': False, 'verified': False},
    {'query': '沥青混凝土小区道路 4cmAC-13上面层+6cmAC-20下面层+20cm水稳基层',
     'category': '市政工程', 'ids': ['2-1-4'], 'note': '标准-沥青道路',
     'ambiguous': False, 'verified': False},
    {'query': 'C25现浇混凝土板 120mm厚 预制空心板 楼板',
     'category': '混凝土工程', 'ids': ['7-3-5', '7-9-1'], 'note': '标准-楼板',
     'ambiguous': True, 'verified': False},
    {'query': 'HRB400钢筋 直径12-18mm 制作安装 圈梁配筋',
     'category': '钢筋工程', 'ids': ['8-1-25'], 'note': '标准-钢筋',
     'ambiguous': False, 'verified': False},
    {'query': '钢制防盗门 甲级 1000x2100 含门框五金',
     'category': '门窗工程', 'ids': ['16-2-3'], 'note': '标准-防盗门',
     'ambiguous': False, 'verified': False},
    {'query': '水泥基渗透结晶防水涂料 卫生间 厚度1.5mm 含管根加强',
     'category': '防水工程', 'ids': ['9-1-8'], 'note': '标准-卫生间防水',
     'ambiguous': False, 'verified': False},
    {'query': '透水砖人行道 60mm厚 1:3水泥砂浆 小区步道',
     'category': '市政工程', 'ids': ['2-3-12'], 'note': '标准-透水砖',
     'ambiguous': False, 'verified': False},
    {'query': '加气混凝土砌块墙 200mm厚 M5混合砂浆 填充墙',
     'category': '砌筑工程', 'ids': ['4-2-1'], 'note': '标准-加气块墙',
     'ambiguous': False, 'verified': False},
    {'query': 'LED平板灯 600x600 36W 嵌入安装 公共走道照明',
     'category': '电气工程', 'ids': ['21-3-5'], 'note': '标准-LED灯',
     'ambiguous': False, 'verified': False},
    {'query': 'PPR冷水管 DN25 暗装敷设 含管件接头',
     'category': '安装工程', 'ids': ['20-1-12'], 'note': '标准-给水管',
     'ambiguous': False, 'verified': False},
    {'query': '乔木种植 胸径10-12cm 国槐 含三角支撑 口袋公园',
     'category': '园林景观', 'ids': ['30-1-8'], 'note': '标准-乔木种植',
     'ambiguous': False, 'verified': False},

    # ── 口语化/方言测试 ──
    {'query': '老楼砖墙370厚 抹水泥20 沈阳1988年砖混外墙翻新',
     'category': '砌筑工程', 'ids': ['4-1-8'], 'note': '口语-砖墙(含抹灰)',
     'ambiguous': False, 'verified': False},
    {'query': '一楼单元门口加个坡道让轮椅能下去 要有扶手',
     'category': '适老化专项', 'ids': ['17-3-1'], 'note': '口语-坡道(含扶手)',
     'ambiguous': False, 'verified': False},
    {'query': '保温板5公分贴外墙 苯板 XPS挤塑板',
     'category': '保温工程', 'ids': ['10-1-36', '10-2-5'], 'note': '口语-保温板50mm',
     'ambiguous': True, 'verified': False},
    {'query': '旧窗户换断桥铝 三层玻璃 70型材 沈阳冬天用',
     'category': '门窗工程', 'ids': ['16-1-8'], 'note': '口语-换窗',
     'ambiguous': False, 'verified': False},
    {'query': '电梯井道用钢结构 玻璃围护 Q235B 6层',
     'category': '钢结构工程', 'ids': ['5-3-12'], 'note': '口语-电梯',
     'ambiguous': False, 'verified': False},
    {'query': '老小区屋顶漏水 做SBS防水卷材 4个厚',
     'category': '防水工程', 'ids': ['9-2-22'], 'note': '口语-屋面防水',
     'ambiguous': False, 'verified': False},
    {'query': '楼梯间刷乳胶漆 刮腻子 两遍 白色',
     'category': '涂料工程', 'ids': ['15-3-10'], 'note': '口语-乳胶漆',
     'ambiguous': False, 'verified': False},
    {'query': '门口路面铺沥青 小区车行道 底下水稳20公分',
     'category': '市政工程', 'ids': ['2-1-4'], 'note': '口语-道路',
     'ambiguous': False, 'verified': False},
    {'query': '卫生间做防水 JS涂料 刷两遍 管根加强',
     'category': '防水工程', 'ids': ['9-1-12'], 'note': '口语-卫生间防水',
     'ambiguous': False, 'verified': False},
    {'query': '室外不锈钢扶手 保温包裹 电伴热 防冻处理 沈阳-15度',
     'category': '适老化专项', 'ids': ['17-2-8'], 'note': '口语-寒地扶手',
     'ambiguous': False, 'verified': False},
]


# ── Ablation configurations ─────────────────────────────────────────────────
# A: pure TF-IDF; B: +keyword; C: +param; D: full fusion. Renormalized so each
# experiment sums to 1.0; D is the module default.
ABLATION_CONFIGS = {
    'A_纯TFIDF':        (1.00, 0.00, 0.00, 0.00),
    'B_TFIDF+关键词':   (0.60, 0.40, 0.00, 0.00),
    'C_TFIDF+参数':     (0.60, 0.00, 0.40, 0.00),
    'D_完整融合':       (0.40, 0.25, 0.25, 0.10),
}


def _ranked_matches(query, top_k, weights):
    start = time.perf_counter()
    matches = match_quota(query, top_k=top_k, weights=weights)
    elapsed = (time.perf_counter() - start) * 1000
    return matches, elapsed


def _hits(predicted_ids, expected_ids):
    """Return the expected ids that appear in the predicted list, preserving
    predicted order (first occurrence).
    """
    return [pid for pid in predicted_ids if pid in expected_ids]


def topk_accuracy(per_case, level, k):
    """Top-k accuracy over ``per_case`` results.

    ``level`` is 'category' (top prediction's specialty equals expected) or
    'id' (any expected resource 编号 appears in top-k predictions).
    """
    n = len(per_case)
    if n == 0:
        return 0.0
    hits = 0
    for r in per_case:
        if level == 'category':
            predicted_cats = [m['quota']['category'] for m in r['matches'][:k]]
            if predicted_cats and predicted_cats[0] == r['expected_category']:
                hits += 1
        else:  # id
            predicted_ids = [m['quota']['id'] for m in r['matches'][:k]]
            if _hits(predicted_ids, r['ids']):
                hits += 1
    return hits / n


def precision_at_k(per_case, k):
    """Mean precision@k at the resource-id level."""
    if not per_case:
        return 0.0
    tot = 0.0
    for r in per_case:
        predicted = [m['quota']['id'] for m in r['matches'][:k]]
        tot += len(set(predicted) & set(r['ids'])) / k
    return tot / len(per_case)


def recall_at_k(per_case, k):
    """Mean recall@k at the resource-id level (fraction of expected ids found)."""
    if not per_case:
        return 0.0
    tot = 0.0
    for r in per_case:
        predicted = [m['quota']['id'] for m in r['matches'][:k]]
        found = len(set(predicted) & set(r['ids']))
        tot += found / len(r['ids'])
    return tot / len(per_case)


def mean_reciprocal_rank(per_case, k):
    """Mean Reciprocal Rank at the resource-id level over top-k predictions."""
    if not per_case:
        return 0.0
    tot = 0.0
    for r in per_case:
        predicted = [m['quota']['id'] for m in r['matches'][:k]]
        rr = 0.0
        for rank, pid in enumerate(predicted, start=1):
            if pid in r['ids']:
                rr = 1.0 / rank
                break
        tot += rr
    return tot / len(per_case)


def _run_cases(weights, top_k=3):
    """Run every labeled case and return per-case result dicts."""
    per_case = []
    for case in LABELED_TEST_CASES:
        query = case['query']
        matches, elapsed = _ranked_matches(query, top_k, weights)
        top = matches[0] if matches else None
        per_case.append({
            'query': query,
            'expected_category': case['category'],
            'ids': case['ids'],
            'note': case['note'],
            'ambiguous': case['ambiguous'],
            'verified': case['verified'],
            'matches': matches,
            'top_category': top['quota']['category'] if top else None,
            'top_id': top['quota']['id'] if top else None,
            'top_name': top['quota']['name'] if top else None,
            'confidence': top['confidence'] if top else 0.0,
            'reliability': top['reliability'] if top else 'none',
            'time_ms': elapsed,
        })
    return per_case


def _summarize(per_case, top_k=3):
    """Compute the full metric table for a set of per-case results."""
    cat_top1 = topk_accuracy(per_case, 'category', 1)
    cat_top3 = topk_accuracy(per_case, 'category', 3)
    id_top1 = topk_accuracy(per_case, 'id', 1)
    id_top3 = topk_accuracy(per_case, 'id', 3)
    return {
        'n_cases': len(per_case),
        'category_top1': cat_top1,
        'category_top3': cat_top3,
        'id_top1': id_top1,
        'id_top3': id_top3,
        'precision@1': precision_at_k(per_case, 1),
        'recall@3': recall_at_k(per_case, 3),
        'mrr': mean_reciprocal_rank(per_case, top_k),
        'avg_time_ms': (sum(r['time_ms'] for r in per_case) / len(per_case)
                        if per_case else 0.0),
        'avg_confidence': (sum(r['confidence'] for r in per_case) / len(per_case)
                           if per_case else 0.0),
    }


def run_full_tests(verbose=True, weights=None, top_k=3, csv_path=None):
    """Run the labeled test set and report category vs resource-id accuracy.

    Returns ``(summary, per_case)``. If ``csv_path`` is given, per-case results
    are exported as UTF-8 CSV.
    """
    per_case = _run_cases(weights, top_k=top_k)
    summary = _summarize(per_case, top_k=top_k)

    if csv_path is not None:
        _export_csv(per_case, csv_path)

    if verbose:
        _print_report(summary, per_case, top_k)
    return summary, per_case


def run_ablation(verbose=True, top_k=3, csv_path=None):
    """Compare A/B/C/D scoring configurations on the same labeled test set.

    Returns a list of ``(config_name, summary)`` tuples.
    """
    rows = []
    for name, w in ABLATION_CONFIGS.items():
        per_case = _run_cases(w, top_k=top_k)
        summary = _summarize(per_case, top_k=top_k)
        rows.append((name, summary))
        if verbose:
            s = summary
            print(f"  {name:<16s} 类别Top1 {s['category_top1']*100:5.1f}%  "
                  f"资源Top1 {s['id_top1']*100:5.1f}%  Top3 {s['id_top3']*100:5.1f}%  "
                  f"MRR {s['mrr']:.3f}  {s['avg_time_ms']:.2f}ms")

    if csv_path is not None:
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['配置', '类别Top1', '类别Top3', '资源Top1', '资源Top3',
                             'Precision@1', 'Recall@3', 'MRR', '平均耗时ms', '平均置信度'])
            for name, s in rows:
                writer.writerow([
                    name,
                    f"{s['category_top1']:.4f}", f"{s['category_top3']:.4f}",
                    f"{s['id_top1']:.4f}", f"{s['id_top3']:.4f}",
                    f"{s['precision@1']:.4f}", f"{s['recall@3']:.4f}",
                    f"{s['mrr']:.4f}", f"{s['avg_time_ms']:.2f}",
                    f"{s['avg_confidence']:.1f}",
                ])
    return rows


def _export_csv(per_case, path):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['序号', '查询', '期望类别', '期望资源编号', '是否歧义',
                         '预测Top1类别', '预测Top1编号', '预测Top1名称',
                         '置信度', '可靠性', '类别正确', '资源正确', '耗时ms', '备注'])
        for i, r in enumerate(per_case, start=1):
            predicted_ids = [m['quota']['id'] for m in r['matches'][:3]]
            writer.writerow([
                i, r['query'], r['expected_category'], '|'.join(r['ids']),
                '是' if r['ambiguous'] else '否',
                r['top_category'], r['top_id'], r['top_name'],
                f"{r['confidence']:.1f}", r['reliability'],
                '是' if r['top_category'] == r['expected_category'] else '否',
                '是' if _hits(predicted_ids, r['ids']) else '否',
                f"{r['time_ms']:.2f}", r['note'],
            ])


def _print_report(summary, per_case, top_k):
    s = summary
    n = s['n_cases']
    n_amb = sum(1 for r in per_case if r['ambiguous'])
    n_std = sum(1 for r in per_case if r['note'].startswith('标准'))
    n_col = sum(1 for r in per_case if r['note'].startswith('口语'))

    print("=" * 92)
    print("  Engineering Resource Matching - Evaluation Report")
    print("=" * 92)
    print(f"  资源库: {len(QUOTA_DB)} 条 | "
          f"{len(set(q['category'] for q in QUOTA_DB))} 个专业")
    print(f"  测试集: {n} 条 (标准 {n_std} + 口语 {n_col}) | "
          f"歧义标注 {n_amb} 条 | 全部待人工复核")
    print("-" * 92)
    print("  【类别匹配率】(原 96.7% 的真实口径)")
    print(f"    Top-1 类别正确: {s['category_top1']*100:.1f}%")
    print(f"    Top-3 类别正确: {s['category_top3']*100:.1f}%")
    print("-" * 92)
    print("  【资源编号匹配率】(best-effort 标注, 需人工复核)")
    print(f"    Top-1 资源正确: {s['id_top1']*100:.1f}%")
    print(f"    Top-3 资源正确: {s['id_top3']*100:.1f}%")
    print(f"    Precision@1: {s['precision@1']:.3f}   Recall@3: {s['recall@3']:.3f}")
    print(f"    MRR@{top_k}: {s['mrr']:.3f}")
    print("-" * 92)
    print(f"  平均置信度: {s['avg_confidence']:.1f}%   平均耗时: {s['avg_time_ms']:.3f}ms/条")
    print("=" * 92)

    print(f"\n  {'状态':<6s}{'查询':<34s}{'期望类别':<10s}{'预测Top1编号':<16s}"
          f"{'置信':>5s}")
    print("  " + "-" * 84)
    for r in per_case:
        cat_ok = r['top_category'] == r['expected_category']
        id_ok = bool(_hits([m['quota']['id'] for m in r['matches'][:top_k]], r['ids']))
        if id_ok:
            tag = "[OK]"
        elif cat_ok:
            tag = "[~]"
        else:
            tag = "[XX]"
        print(f"  {tag:<6s}{r['query'][:32]:<34s}{r['expected_category']:<10s}"
              f"{r['top_id'] or 'N/A':<16s}{r['confidence']:>4.1f}%")
    print("\n  [OK]=资源编号命中  [~]=仅类别命中  [XX]=未命中")


def demonstrate():
    """Interactive demo showing representative matches and change predictions."""
    from .matching import predict_change

    print("\n" + "=" * 80)
    print("  Engineering Resource Matching - TF-IDF engine")
    print(f"  Resource library: {len(QUOTA_DB)} entries | "
          f"{len(set(q['category'] for q in QUOTA_DB))} specialties")
    print("  Algorithm: TF-IDF + keyword + dimension + category fusion")
    print("=" * 80)

    demos = [
        ("370mm实心砖墙 M5混合砂浆 MU10 沈阳1988年砖混外墙", "Wall-001"),
        ("C25现浇混凝土构造柱 240x240 抗震设防7度 336根", "Col-003"),
        ("不锈钢无障碍扶手D38/D50 含L型支架 楼梯间", "Handrail"),
        ("老楼砖墙370厚 抹水泥20 翻新改造", "colloquial"),
        ("单元门口加个坡道 让轮椅能下去", "colloquial"),
    ]

    for text, context in demos:
        print(f"\n  [{context}]")
        print(f"  Input: {text}")
        matches = match_quota(text, top_k=3)
        if matches:
            best = matches[0]
            tag = best["reliability"]
            print(f"  [{tag}] [{best['quota']['id']}] {best['quota']['name']}")
            print(f"  Unit price: {best['quota']['unit_price']:.2f} yuan/{best['quota']['unit']} "
                  f"| {best['confidence']:.1f}%")
            if best["reliability"] == "low":
                print("  WARNING: low confidence, manual review recommended")
            if len(matches) > 1:
                alts = ', '.join('[%s]%.0f%%' % (m['quota']['id'], m['confidence'])
                                 for m in matches[1:])
                print(f"  Alternatives: {alts}")

    print("\n  -- Change-cost prediction --")
    preds = [
        ("扶手加装", 350, "不锈钢扶手D38"),
        ("管线迁改", 500, "地下综合管沟"),
        ("广场变更", 800, "铺装材料"),
    ]
    for ct, area, comp in preds:
        p = predict_change(ct, area, comp)
        print(f"  {ct} {area}m2 {comp}: {p['risk_tag']} {p['predicted_level']} | "
              f"~{p['predicted_amount']:.0f} wan | {p['confidence'] * 100:.0f}%")

    print("\n" + "=" * 80)
    print("  Metrics are reported by run_full_tests(); see README for numbers.")
    print("=" * 80)
