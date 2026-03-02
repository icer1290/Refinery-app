"""
数据生成脚本
执行完整数据流程但不发送邮件

流程:
1. 数据摄入 (ingest_and_store)
2. Agent 节点 1-4 (fetch_data -> scoring -> deep_extraction -> summarize)
3. 保存结果到文件
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline.ingest_and_store import fetch_all_data, merge_all_articles, process_and_store
from src.agent.state import create_initial_state
from src.agent.nodes import (
    fetch_data_node,
    scoring_node,
    deep_extraction_node,
    summarize_node
)
import json


def run_ingestion():
    """执行数据摄入"""
    print("\n" + "=" * 60)
    print("步骤 1: 数据摄入")
    print("=" * 60)

    rss_feeds_data = fetch_all_data()
    all_articles = merge_all_articles(rss_feeds_data)

    if not all_articles:
        print("X 没有获取到任何数据")
        return None

    stats = process_and_store(all_articles, clear_collection=True)
    return stats


def run_agent_workflow():
    """执行 Agent 工作流（跳过 delivery）"""
    print("\n" + "=" * 60)
    print("步骤 2: Agent 工作流")
    print("=" * 60)

    state = create_initial_state()

    # 节点 1: fetch_data
    print("\n[1/4] fetch_data_node")
    state = fetch_data_node(state)
    if not state["candidate_pool"]:
        print("X 没有获取到新闻数据，终止流程")
        return None

    # 节点 2: scoring
    print("\n[2/4] scoring_node")
    state = scoring_node(state)
    if not state["top_articles"]:
        print("X 打分后没有文章，终止流程")
        return None

    # 节点 3: deep_extraction
    print("\n[3/4] deep_extraction_node")
    state = deep_extraction_node(state)
    if not state["top_articles"]:
        print("X 正文提取失败，终止流程")
        return None

    # 节点 4: summarize
    print("\n[4/4] summarize_node")
    state = summarize_node(state)

    return state


def save_results(state):
    """保存结果到文件"""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 保存 JSON
    json_file = os.path.join(output_dir, f"news_data_{date_str}.json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({
            "top_articles": state["top_articles"],
            "summaries": state["summaries"],
            "error_logs": state["error_logs"]
        }, f, ensure_ascii=False, indent=2)
    print(f"+ JSON 已保存: {json_file}")

    # 保存简易 HTML
    html_file = os.path.join(output_dir, f"news_preview_{date_str}.html")
    html_content = generate_simple_html(state["top_articles"])
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"+ HTML 已保存: {html_file}")


def generate_simple_html(articles):
    """生成简易 HTML 预览"""
    html = ["<!DOCTYPE html>", "<html><head><meta charset='utf-8'>",
            "<title>科技新闻日报</title></head><body>"]
    html.append(f"<h1>科技新闻日报 - {datetime.now().strftime('%Y-%m-%d')}</h1>")

    for i, article in enumerate(articles, 1):
        html.append(f"<h2>{i}. {article.get('title', 'N/A')}</h2>")
        html.append(f"<p><a href='{article.get('url', '#')}'>{article.get('url', 'N/A')}</a></p>")
        html.append(f"<p><b>来源:</b> {article.get('source', 'N/A')} | <b>分数:</b> {article.get('final_score', 0):.2f}</p>")
        if article.get('generated_summary'):
            html.append(f"<p><b>摘要:</b> {article.get('generated_summary')}</p>")
        html.append("<hr>")

    html.append("</body></html>")
    return "\n".join(html)


def main():
    print("=" * 60)
    print("科技新闻数据生成脚本")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 步骤 1: 数据摄入
    stats = run_ingestion()
    if stats is None:
        print("\nX 数据摄入失败，终止流程")
        return

    # 步骤 2: Agent 工作流
    state = run_agent_workflow()
    if state is None:
        print("\nX Agent 工作流失败")
        return

    # 步骤 3: 保存结果
    print("\n" + "=" * 60)
    print("步骤 3: 保存结果")
    print("=" * 60)
    save_results(state)

    # 总结
    print("\n" + "=" * 60)
    print("完成统计")
    print("=" * 60)
    print(f"摄入文章: {stats['total_input']} 条")
    print(f"去重后: {stats['new_inserted']} 条")
    print(f"处理文章: {len(state['top_articles'])} 条")
    print(f"错误数: {len(state['error_logs'])} 条")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("+ 数据生成完成！")


if __name__ == "__main__":
    main()