# TFIDF-Engineering-Resource-Matching

基于 **TF-IDF** 的工程资源语义匹配工具。将自由文本（常含口语化表达）的中文工程描述转化为 TF-IDF 向量，并通过「余弦相似度 + 关键词增强 + 尺寸匹配」的融合评分对候选资源进行排序匹配。

> [English](README.md) | **中文文档**

---

## 项目概述

在工程造价与 BIM 工程项目管理中，一个反复出现的瓶颈是：把构件的自然语言描述（一面墙、一根柱、一段扶手、一段道路……）映射到带编码和单价的**结构化资源条目**上。传统做法是人工翻定额、读描述、挑子目。

本项目用一条轻量、可解释的 NLP 流水线替代人工查找：**文本归一化 → 分词 → TF-IDF 加权 → 融合相似度排序**。项目内置一个覆盖 **21 个专业、202 条**的示例资源库，开箱即用。

## 研究背景

- **领域痛点**：「定额匹配」是造价管理中最基础、最高频、又最依赖人工经验的工作。人工匹配单条约需 2–3 分钟，且不同造价员的判定结果不一致。
- **为何选 TF-IDF**：经典 TF-IDF + 余弦相似度可解释、几乎零训练成本，配合领域同义词归一化，能很好地处理工程文本「短、术语密集」的特点，是升级到 BERT 等重模型前务实的基线方案。

## 问题定义

> 给定一条自然语言的工程资源描述（可能含口语化、简写），在结构化资源库中找出最相关的条目，并给出带置信度的排序结果。

具体需处理：

- 标准描述：`370mm实心砖墙 M5混合砂浆 砖混住宅`
- 口语/简写输入：`老楼砖墙370厚 抹水泥20 翻新`
- 尺寸敏感查询：厚度、截面、数量、层数。

## 主要功能

- **文本归一化** —— 口语→标准词映射、厚度写法统一（`370厚`→`370mm`）、中文数字统一。
- **稳健分词** —— 优先 jieba，未安装时自动回退到内置正则分词。
- **TF-IDF 向量化** —— 对资源库语料做平滑 IDF 加权。
- **融合评分** —— 余弦相似度（0.65）+ 关键词增强（0.20）+ 尺寸匹配（0.15）。
- **置信度与可靠性** —— 每条匹配结果附带百分比置信度和 高/中/低 可靠性标签。
- **变更造价预测** —— 附加模块，用 TF-IDF 相似度把「变更类型+面积」映射到造价档位。
- **可选 Gradio 网页演示** —— 交互式浏览器界面。

## 技术框架

```
描述 ─▶ 归一化 ─▶ 分词 ─▶ TF-IDF 向量
                            │
          余弦相似度 (0.65) ─┤
          关键词增强 (0.20) ─┼──▶ 综合得分 ─▶ 排序 ─▶ Top-k
          尺寸匹配 (0.15) ──┘
```

| 模块                | 职责                                   |
|---------------------|----------------------------------------|
| `preprocessing.py`  | 归一化、分词                           |
| `tfidf.py`          | IDF 与 TF-IDF 向量计算                 |
| `similarity.py`     | 余弦相似度、尺寸与关键词启发式         |
| `quota_db.py`       | 202 条资源库                           |
| `matching.py`       | `match_quota` 与 `predict_change`      |
| `evaluation.py`     | 30 条测试集与演示                      |
| `web.py`            | Gradio 网页演示                        |

## 项目结构

```
TFIDF-Engineering-Resource-Matching/
├── README.md               # 英文说明
├── README_CN.md            # 本文件
├── LICENSE                 # MIT
├── requirements.txt
├── main.py                 # 命令行入口
├── pytest.ini
├── src/                    # 核心库
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
│   ├── quota_database.csv  # 导出的资源库
│   ├── sample_queries.csv  # 30 条测试查询
│   └── README.md
├── tests/                  # pytest 测试套件
├── examples/               # 使用示例
├── docs/                   # 算法 / 方法 / 使用说明
├── results/                # 示例结果 + 实验报告
├── images/                 # 生成的示意图
└── scripts/                # 数据/图表导出脚本
```

## 安装

需要 Python 3.8+。

```bash
git clone https://github.com/Willow0430/TFIDF-Engineering-Resource-Matching.git
cd TFIDF-Engineering-Resource-Matching
pip install -r requirements.txt
```

`jieba` 是唯一核心依赖；未安装时匹配器会自动回退到正则分词。`gradio` 与
`matplotlib` 为可选项。

## 快速开始

```bash
# 运行内置评测套件（30 条用例）
python main.py --report

# 交互式命令行演示
python main.py --demo

# 启动网页演示
python main.py --web
```

## 使用示例

```python
from src import match_quota, predict_change, normalize_query

# 标准描述
for m in match_quota("370mm实心砖墙 M5混合砂浆 砖混住宅", top_k=3):
    print(m["quota"]["id"], m["quota"]["name"], f"{m['confidence']:.1f}%")

# 口语描述（自动归一化）
print(normalize_query("老楼砖墙370厚 抹水泥20 翻新"))

# 变更造价预测
print(predict_change("扶手加装", 350, "不锈钢扶手D38"))
```

可运行版本见 `examples/example.py`。

## 示例结果

对内置 30 条用例（20 标准 + 10 口语）的实测结果：

| 指标                          | 结果             |
|-------------------------------|------------------|
| 总体准确率（Top-1）            | **29/30 = 96.7%** |
| 标准用例（Top-1）              | 20/20 = 100.0%   |
| 口语化用例（Top-1）            | 9/10 = 90.0%     |
| 平均置信度                     | 47.2%            |
| 平均耗时                       | 约 26 ms/条      |

唯一误匹配是口语用例 `一楼单元门口加个坡道让轮椅能下去 要有扶手`，被匹配到了
「门窗工程」而非「适老化专项」。逐条明细见 `results/sample_result.csv` 与
`results/experiment_report.md`。

## 局限性

- **词袋模型**：TF-IDF 不考虑词序，长句或歧义描述精度会下降。
- **领域数据为精选子集**：内置库为 202 条精选条目，并非完整省级定额；价格为示意值。
- **口语覆盖不完整**：同义词词典能覆盖常见口语，但无法覆盖任意方言或缩写。
- **缺乏真实语义理解**：超出同义词映射范围的改写无法命中，升级到词嵌入模型是自然的方向。

## 未来开发

- 将匹配核心升级为 BERT / 句向量模型，提升口语化覆盖。
- 支持从用户提供的 CSV 加载资源库，替代硬编码模块。
- 增加复合组价逻辑（如 墙体 = 砌筑 + 保温 + 饰面）。
- 在更大规模、带标注的语料上做基准测试。

## 许可证

MIT —— 见 [LICENSE](LICENSE)。内置资源库为精选子集，源自公开出版的
《辽宁省建设工程计价定额（2024 版）》与沈阳市材料信息价；再分发数据前请核实
来源的使用条款。
