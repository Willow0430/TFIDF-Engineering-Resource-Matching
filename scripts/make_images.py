# -*- coding: utf-8 -*-
"""Generate the three project diagrams in images/.

Run from the project root:

    python scripts/make_images.py

Outputs:
    images/project_overview.png   - overall technical route
    images/workflow.png           - algorithm flow chart
    images/matching_result.png    - real top-5 match confidence bars
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Chinese-capable font on Windows.
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")

BLUE = "#1a73e8"
LIGHT = "#e8f0fe"
GREEN = "#188038"
LIGHT_GREEN = "#e6f4ea"
ORANGE = "#e8710a"
LIGHT_ORANGE = "#fef3e6"


def _box(ax, x, y, w, h, text, fc=LIGHT, ec=BLUE, fs=10):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec=ec, lw=1.5))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def _arrow(ax, p1, p2, color="#444"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=16,
                                 lw=1.6, color=color))


def _finish(fig, path):
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote %s" % os.path.relpath(path, ROOT))


def project_overview():
    fig, ax = plt.subplots(figsize=(8, 9.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis("off")

    ax.text(5, 13.4, "TF-IDF 工程资源匹配 · 技术路线", ha="center", va="center",
            fontsize=15, weight="bold", color="#202124")

    steps = [
        ("① 工程资源描述（输入）", "自然语言 / 口语化构件描述", LIGHT_ORANGE, ORANGE),
        ("② 文本预处理 preprocessing", "口语归一化 + jieba分词（正则回退）", LIGHT, BLUE),
        ("③ TF-IDF 向量化 tfidf", "平滑IDF + TF·IDF 加权", LIGHT, BLUE),
        ("④ 融合评分 matching", "0.65余弦 + 0.20关键词 + 0.15尺寸", LIGHT_GREEN, GREEN),
        ("⑤ 排序输出（Top-k）", "置信度 + 高/中/低可靠性", LIGHT_GREEN, GREEN),
    ]

    y = 12.2
    h = 1.7
    gap = 0.75
    centers = []
    for title, sub, fc, ec in steps:
        _box(ax, 1.2, y, 7.6, h, title + "\n" + sub, fc=fc, ec=ec, fs=11)
        centers.append(y + h / 2)
        y -= (h + gap)

    for i in range(len(centers) - 1):
        _arrow(ax, (5, centers[i] - h / 2 - 0.05), (5, centers[i + 1] + h / 2 + 0.05))

    _finish(fig, os.path.join(IMG, "project_overview.png"))


def workflow():
    fig, ax = plt.subplots(figsize=(8.5, 9))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 13)
    ax.axis("off")

    ax.text(5.5, 12.3, "匹配算法流程图", ha="center", va="center",
            fontsize=15, weight="bold", color="#202124")

    _box(ax, 2.0, 11.0, 7.0, 1.1, "输入描述  query", LIGHT_ORANGE, ORANGE)
    _arrow(ax, (5.5, 11.0), (5.5, 10.3))
    _box(ax, 2.0, 9.2, 7.0, 1.1, "normalize_query()  口语→标准 / 厚度统一", LIGHT, BLUE)
    _arrow(ax, (5.5, 9.2), (5.5, 8.5))
    _box(ax, 2.0, 7.4, 7.0, 1.1, "tokenize()  jieba 分词 + 单位对提取", LIGHT, BLUE)
    _arrow(ax, (5.5, 7.4), (5.5, 6.7))
    _box(ax, 2.0, 5.6, 7.0, 1.1, "compute_tfidf_vector()  TF·IDF 加权", LIGHT, BLUE)
    _arrow(ax, (5.5, 5.6), (5.5, 4.9))
    _box(ax, 2.0, 3.8, 7.0, 1.1, "对每条资源计算 combined 融合得分", LIGHT_GREEN, GREEN)
    _arrow(ax, (5.5, 3.8), (5.5, 3.1))
    _box(ax, 2.0, 2.0, 7.0, 1.1, "combined > 0.03 ?", "#fff3cd", "#997404")
    # yes / no branches
    _arrow(ax, (2.0, 2.55), (1.0, 1.0))
    _arrow(ax, (9.0, 2.55), (10.0, 1.0))
    ax.text(0.55, 1.6, "否：丢弃", fontsize=9, color="#888", ha="center")
    ax.text(10.45, 1.6, "是：保留", fontsize=9, color="#188038", ha="center")
    _arrow(ax, (5.5, 2.0), (5.5, 1.0))
    _box(ax, 2.6, 0.05, 5.8, 0.95, "按 combined 降序 → Top-k + 置信度", LIGHT_GREEN, GREEN, fs=10.5)

    _finish(fig, os.path.join(IMG, "workflow.png"))


def matching_result():
    from src import match_quota

    query = "370mm实心砖墙 M5混合砂浆 砖混住宅"
    matches = match_quota(query, top_k=5)
    labels = [f"[{m['quota']['id']}] {m['quota']['name'][:20]}" for m in matches]
    confs = [m["confidence"] for m in matches]
    labels = labels[::-1]
    confs = confs[::-1]

    fig, ax = plt.subplots(figsize=(9, 5.2))
    colors = ["#1a73e8", "#4285f4", "#7baaf7", "#aecbfa", "#d2e3fc"]
    bars = ax.barh(labels, confs, color=colors)
    ax.set_xlabel("置信度 (%)")
    ax.set_title(f"匹配结果展示：{query}", fontsize=12)
    ax.set_xlim(0, max(confs) * 1.25)
    for b, c in zip(bars, confs):
        ax.text(b.get_width() + 1, b.get_y() + b.get_height() / 2,
                f"{c:.1f}%", va="center", fontsize=9)
    ax.tick_params(axis="y", labelsize=9)
    fig.tight_layout()
    _finish(fig, os.path.join(IMG, "matching_result.png"))


if __name__ == "__main__":
    os.makedirs(IMG, exist_ok=True)
    project_overview()
    workflow()
    matching_result()
