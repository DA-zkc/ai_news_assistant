"""
Streamlit 应用入口：AI 要闻助手 Web 版

使用方式：
    streamlit run streamlit_app.py

页面会通过现有模块调用完整的新闻处理流水线，生成要闻摘要并支持 Markdown 下载。
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from modules.fetcher import fetch_news, NewsAPIError
from modules.filter import filter_news, FilterError
from modules.fact_opinion import process as process_fact_opinion, FactOpinionError
from modules.core_event import extract as extract_core_event, CoreEventError
from modules.merger import merge_and_score, MergerError
from modules.output import generate_markdown, OutputError


def run_pipeline(date, lang, country, max_articles, eps, no_qwen):
    result = {
        "raw_news": [],
        "filtered_news": [],
        "analyzed_news": [],
        "core_events": [],
        "merged_events": [],
        "markdown": "",
        "error": None,
    }

    try:
        raw_news = fetch_news(
            query="artificial intelligence",
            lang=lang,
            country=country,
            max_articles=max_articles,
            sort_by="publishedAt",
            date=date,
        )
        if not raw_news:
            raise NewsAPIError("未能获取任何新闻，请检查 API 配置或调整语言/国家选项")
        result["raw_news"] = raw_news

        filtered_news = filter_news(raw_news)
        if not filtered_news:
            raise FilterError("筛选后没有符合条件的新闻")
        result["filtered_news"] = filtered_news

        analyzed_news = process_fact_opinion(filtered_news)
        if not analyzed_news:
            raise FactOpinionError("事实观点分析失败")
        result["analyzed_news"] = analyzed_news

        core_events = extract_core_event(analyzed_news)
        if not core_events:
            raise CoreEventError("核心事件提取失败")
        result["core_events"] = core_events

        merged_events = merge_and_score(core_events, eps=eps, use_qwen_description=not no_qwen)
        if not merged_events:
            raise MergerError("事件合并失败")
        result["merged_events"] = merged_events

        markdown_content = generate_markdown(merged_events, date=date)
        if not markdown_content:
            raise OutputError("Markdown 生成失败")
        result["markdown"] = markdown_content

    except Exception as err:
        result["error"] = err

    return result


def format_article(article):
    return f"- [{article['title']}]({article['url']}) \n  - {article['source_name']} | {article['published_at']}"


def main():
    st.set_page_config(
        page_title="AI 要闻助手",
        page_icon="🤖",
        layout="wide",
    )

    st.title("🤖 AI 要闻助手 Web 版")
    st.markdown(
        "通过 Streamlit 将现有新闻采集、过滤、事实观点分析、核心事件提取和事件合并流水线可视化。"
    )

    with st.sidebar:
        st.header("运行参数")
        date = st.date_input("日期", datetime.now()).strftime("%Y-%m-%d")
        lang = st.selectbox("语言", ["en", "zh"], index=0)
        country = st.text_input("国家代码 (可选)", value="")
        max_articles = st.slider("最大文章数", min_value=10, max_value=200, value=100, step=10)
        eps = st.slider("事件聚类 eps", min_value=0.1, max_value=1.0, value=0.3, step=0.05)
        no_qwen = st.checkbox("禁用 Qwen 描述生成", value=False)
        run_button = st.button("开始生成")

    if run_button:
        country_value = country.strip() or None
        st.info("开始执行 AI 新闻流水线，请稍候... 无法获得结果时请检查 API KEY 和网络连接。")

        with st.spinner("正在拉取并处理新闻..."):
            result = run_pipeline(
                date=date,
                lang=lang,
                country=country_value,
                max_articles=max_articles,
                eps=eps,
                no_qwen=no_qwen,
            )

        if result["error"]:
            st.error(f"❌ 处理失败: {result['error']}")
            if isinstance(result["error"], NewsAPIError):
                st.warning("请检查 GNews API Token、语言和国家参数。")
            return

        st.success("✅ 处理完成！")
        st.markdown(f"**原始新闻数量**: {len(result['raw_news'])}  ")
        st.markdown(f"**筛选后新闻**: {len(result['filtered_news'])}  ")
        st.markdown(f"**已分析新闻**: {len(result['analyzed_news'])}  ")
        st.markdown(f"**核心事件数**: {len(result['core_events'])}  ")
        st.markdown(f"**最终事件数**: {len(result['merged_events'])}  ")

        st.subheader("最终事件摘要")
        for idx, event in enumerate(result["merged_events"], start=1):
            st.markdown(f"**{idx}. {event.get('title', '事件')}**")
            st.write(event.get("description", "暂无描述"))
            st.write(f"来源数量: {len(event.get('sources', []))}")
            st.markdown("---")

        st.subheader("输出 Markdown")
        st.code(result["markdown"], language="markdown")
        st.download_button(
            label="下载 Markdown 文件",
            data=result["markdown"].encode("utf-8"),
            file_name=f"ai_news_{date}.md",
            mime="text/markdown",
        )

        with st.expander("查看原始新闻标题"):
            for article in result["raw_news"][:20]:
                st.markdown(format_article(article))


if __name__ == "__main__":
    main()
