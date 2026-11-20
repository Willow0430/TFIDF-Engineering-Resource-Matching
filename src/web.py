# -*- coding: utf-8 -*-
"""Optional Gradio web demo.

Provides an interactive browser UI for the matcher and the change-cost
predictor. Requires ``gradio`` (installed via ``pip install gradio``).
"""

from .matching import match_quota, predict_change, QUOTA_DB
from .preprocessing import normalize_query


def build_web_demo(share=False):
    """Build and launch the Gradio web demo."""
    try:
        import gradio as gr
    except ImportError:  # pragma: no cover - depends on environment
        print("[hint] Gradio is not installed. Run: pip install gradio")
        return

    def search_quota(query):
        if not query.strip():
            return "", "", "请输入构件描述", ""
        normalized = normalize_query(query)
        matches = match_quota(query, top_k=5)
        if not matches:
            return query, "未找到匹配资源", "建议调整关键词后重试", ""

        best = matches[0]
        tag = {"high": "高", "medium": "中", "low": "低"}[best["reliability"]]
        top_result = "[{}] {}\n置信度: {} | 综合单价: {:.2f}元/{}".format(
            best["quota"]["id"], best["quota"]["name"],
            tag, best["quota"]["unit_price"], best["quota"]["unit"])

        norm_hint = query
        if normalized != query:
            norm_hint = "原始输入: {}\n归一化后: {}".format(query, normalized)

        lines = []
        for i, m in enumerate(matches):
            q = m["quota"]
            tag = {"high": "高", "medium": "中", "low": "低"}[m["reliability"]]
            line = "#{} [{}] {}\n    {}元/{} | 置信度:{:.1f}% | 可靠性:{}".format(
                i + 1, q["id"], q["name"],
                q["unit_price"], q["unit"], m["confidence"], tag)
            lines.append(line)

        return norm_hint, top_result, "\n\n".join(lines), q.get("category", "")

    def do_predict(ct, area, comp):
        if not ct:
            return "请选择变更类型"
        p = predict_change(ct, area, comp)
        return "风险: {} | 档位: {}\n预计: {:.0f}万 | 置信度: {:.0f}%".format(
            p["risk_tag"], p["predicted_level"],
            p["predicted_amount"], p["confidence"] * 100)

    with gr.Blocks(title="Engineering Resource Matching") as demo:
        gr.Markdown("""
        # Engineering Resource Matching (TF-IDF)
        NLP-driven resource matching + change-cost prediction.

        **Algorithm:** TF-IDF + keyword boost + dimension match + normalization
        | **Resource library:** {} entries / {} specialties
        """.format(len(QUOTA_DB), len(set(q['category'] for q in QUOTA_DB))))

        with gr.Tab("Resource Matching"):
            gr.Markdown("Enter a natural-language description (colloquial input is supported) "
                        "and get the top resource matches with confidence scores.")
            with gr.Row():
                query_input = gr.Textbox(
                    label="Description",
                    placeholder="e.g. 370mm实心砖外墙 M5混合砂浆 砖混住宅\n"
                                "colloquial: 老楼砖墙370厚 抹水泥20",
                    lines=3, scale=3)
                norm_output = gr.Textbox(label="Normalized", lines=3, scale=2)
            btn = gr.Button("Match", variant="primary", size="lg")

            with gr.Row():
                top_result = gr.Textbox(label="Best match", lines=3, scale=2)
                top_detail = gr.Textbox(label="Unit price", scale=1)

            gr.Markdown("---")
            results_output = gr.Textbox(label="Results (Top 5)", lines=10)

            btn.click(fn=search_quota, inputs=[query_input],
                      outputs=[norm_output, top_result, results_output, top_detail])

            gr.Examples(
                examples=[
                    "370mm实心砖墙 M5混合砂浆 MU10 砖混住宅",
                    "C25钢筋混凝土构造柱 240x240 抗震7度",
                    "外墙30mm挤塑聚苯板保温 聚合物砂浆 网格布",
                    "SBS改性沥青防水卷材 4mm厚 II型 屋面热熔法",
                    "老楼砖墙370厚 抹水泥20 保温也一起弄",
                    "旧窗户换断桥铝 双层玻璃 70型材",
                    "一楼单元门口加个坡道让轮椅能下去 要带扶手不锈钢的",
                ],
                inputs=[query_input],
            )

        with gr.Tab("Change-cost Prediction"):
            gr.Markdown("Input a change type + area + component to predict cost band and risk level.")
            with gr.Row():
                ct_input = gr.Dropdown(
                    label="Change type",
                    choices=["扶手加装", "管线迁改", "外墙涂料变更", "门窗更换", "电梯加装",
                             "道路拓宽", "绿化提升", "结构加固", "保温升级", "防水翻修",
                             "坡道改造", "智能化升级", "雨污分流", "屋面翻新", "广场重铺"],
                    value="扶手加装")
                area_input = gr.Number(label="Area (m2)", value=350)
            comp_input = gr.Textbox(label="Key component", value="不锈钢扶手D38")
            pred_btn = gr.Button("Predict", variant="primary")
            pred_output = gr.Textbox(label="Prediction", lines=3)
            pred_btn.click(fn=do_predict, inputs=[ct_input, area_input, comp_input], outputs=[pred_output])

        with gr.Tab("Pipeline"):
            gr.Markdown("""
            ### Text input -> Preprocess -> TF-IDF -> Match -> Rank -> Output

            1. **Input**: natural-language engineering resource description.
            2. **Normalization**: synonym mapping + thickness/numeral unification.
            3. **Tokenization**: jieba (with regex fallback).
            4. **Vectorization**: TF-IDF weighting over the resource corpus.
            5. **Scoring**: cosine similarity + keyword boost + dimension match.
            6. **Output**: ranked resource matches with confidence + unit price.
            """)

    print("Starting web demo...")
    print("Local URL: http://127.0.0.1:7860")
    demo.launch(share=share, server_name="127.0.0.1")
