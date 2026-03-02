"""
LangGraph 节点实现
包含各节点的具体逻辑：fetch_data_node, scoring_node, deep_extraction_node, summarize_node, delivery_node
"""

import sys
import os
from typing import Dict, Any, List
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.agent.state import GraphState
from src.vector_store import get_vector_store


def fetch_data_node(state: GraphState) -> GraphState:
    """
    数据提取节点
    
    从 Qdrant 中提取当日内（UTC+8 时间）所有已入库的新闻元数据。
    按 inserted_at 字段过滤，范围为 UTC+8 时间今日 00:00:00 至 23:59:59。
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态，candidate_pool 包含当日所有新闻
    """
    print("\n" + "=" * 60)
    print("[Node] fetch_data_node - 数据提取")
    print("=" * 60)
    
    try:
        # 初始化 VectorStore
        vector_store = get_vector_store()
        
        # 测试连接
        if not vector_store.test_connection():
            error_msg = "无法连接到 Qdrant 服务"
            print(f"✗ {error_msg}")
            state["error_logs"].append(f"[{datetime.now().isoformat()}] fetch_data_node: {error_msg}")
            state["candidate_pool"] = []
            return state
        
        # 获取当日新闻
        print("\n[1/2] 正在从 Qdrant 获取当日新闻...")
        today_news = vector_store.fetch_today_news()
        
        # 更新状态
        state["candidate_pool"] = today_news
        
        print(f"\n[2/2] 数据提取完成")
        print(f"✓ 成功获取 {len(today_news)} 条当日新闻")
        
        # 显示数据摘要
        if today_news:
            print("\n数据来源分布:")
            source_count = {}
            for news in today_news:
                source = news.get("source", "Unknown")
                source_count[source] = source_count.get(source, 0) + 1
            
            for source, count in sorted(source_count.items(), key=lambda x: -x[1]):
                print(f"  - {source}: {count} 条")
        
    except Exception as e:
        error_msg = f"数据提取失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] fetch_data_node: {error_msg}")
        state["candidate_pool"] = []
    
    return state


def scoring_node(state: GraphState) -> GraphState:
    """
    批量打分与排序节点
    
    对 candidate_pool 中的所有新闻进行打分和排序：
    1. 使用 LLM 对标题和简介进行打分（0-10分）
    2. 实时计算加权得分：Final_Score = (原始热度 / Batch_Max_热度) * 0.3 + (LLM打分 / 10) * 0.7
    3. 按 Final_Score 降序排列，取前 50 名留在 candidate_pool，前 25 名进入 top_articles
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    import asyncio
    from src.llm import get_llm_client
    
    print("\n" + "=" * 60)
    print("[Node] scoring_node - 批量打分与排序")
    print("=" * 60)
    
    candidate_pool = state.get("candidate_pool", [])
    
    # 1. 数据验证
    if not candidate_pool:
        print("✗ candidate_pool 为空，无需打分")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] scoring_node: candidate_pool 为空")
        return state
    
    print(f"\n[1/5] 开始处理 {len(candidate_pool)} 条新闻...")
    
    # 2. 加载 Prompt
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "src", "prompt", "scoring_prompt.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        print(f"✓ 已加载打分 Prompt")
    except Exception as e:
        error_msg = f"加载 Prompt 失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] scoring_node: {error_msg}")
        return state
    
    # 3. 批量 LLM 打分
    print(f"\n[2/5] 正在调用 LLM 进行批量打分 (并发数: 5，带重试)...")
    try:
        llm_client = get_llm_client()
        
        # 运行异步批量打分
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        scored_news = loop.run_until_complete(
            llm_client.batch_score_news(
                news_list=candidate_pool,
                prompt_template=prompt_template,
                max_concurrency=5
            )
        )
        loop.close()
        
        # 统计打分结果
        success_count = sum(1 for news in scored_news if news.get("scoring_error") is None)
        error_count = len(scored_news) - success_count
        
        print(f"✓ 打分完成: {success_count} 成功, {error_count} 失败")
        
        # 记录打分失败的错误
        for news in scored_news:
            if news.get("scoring_error"):
                error_msg = f"新闻打分失败 '{news.get('title', 'Unknown')}': {news['scoring_error']}"
                state["error_logs"].append(f"[{datetime.now().isoformat()}] scoring_node: {error_msg}")
        
    except Exception as e:
        error_msg = f"批量打分失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] scoring_node: {error_msg}")
        return state
    
    # 4. 计算加权得分
    print(f"\n[3/5] 计算加权得分...")
    
    # 找出 Batch 中的最大热度值
    max_raw_score = max(news.get("score", 0) for news in scored_news) if scored_news else 1
    if max_raw_score == 0:
        max_raw_score = 1  # 避免除以零
    
    print(f"  - Batch 最大原始热度: {max_raw_score}")
    
    # 计算加权得分
    for news in scored_news:
        raw_score = news.get("score", 0)
        llm_score = news.get("llm_score", 0)
        
        # Final_Score = (原始热度 / Batch_Max_热度) * 0.3 + (LLM打分 / 10) * 0.7
        normalized_popularity = raw_score / max_raw_score
        normalized_llm_score = llm_score / 10
        final_score = normalized_popularity * 0.3 + normalized_llm_score * 0.7
        
        news["final_score"] = round(final_score, 4)
        news["normalized_popularity"] = round(normalized_popularity, 4)
        news["normalized_llm_score"] = round(normalized_llm_score, 4)
    
    print(f"✓ 加权得分计算完成")
    
    # 5. 排序筛选
    print(f"\n[4/5] 排序并筛选 Top 新闻...")
    
    # 按 Final_Score 降序排列
    sorted_news = sorted(scored_news, key=lambda x: x.get("final_score", 0), reverse=True)
    
    # 取前 50 名留在 candidate_pool
    top_50 = sorted_news[:50]
    state["candidate_pool"] = top_50

    # 取前 25 名进入 top_articles
    top_25 = sorted_news[:25]
    state["top_articles"] = top_25

    print(f"✓ 筛选完成: Top 50 留在 candidate_pool, Top 25 进入 top_articles")
    
    # 6. 输出摘要
    print(f"\n[5/5] 打分结果摘要:")
    print(f"  - 总计处理: {len(scored_news)} 条")
    print(f"  - 成功打分: {success_count} 条")
    print(f"  - 进入候选池 (Top 50): {len(top_50)} 条")
    print(f"  - 进入深度提取 (Top 25): {len(top_25)} 条")

    print(f"\n  Top 5 新闻:")
    for i, news in enumerate(top_25[:5], 1):
        print(f"    {i}. [{news.get('final_score', 0):.2f}] {news.get('title', 'Unknown')[:50]}...")
        print(f"       分类: {news.get('category', '其他')} | 理由: {news.get('reason', 'N/A')[:30]}...")
    
    return state


def deep_extraction_node(state: GraphState) -> GraphState:
    """
    深度提取节点

    使用 trafilatura 并发抓取 Top 25 条目的正文：
    - 使用 asyncio.Semaphore(5) 限制并发
    - 抓取失败的 URL 记录到 error_logs
    - 从 candidate_pool 第 16 名开始顺序补齐
    - 保留完整 Markdown 内容，不截断
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态，top_articles 包含正文内容
    """
    import asyncio
    from src.extraction import batch_extract_articles
    from datetime import datetime
    
    print("\n" + "=" * 60)
    print("[Node] deep_extraction_node - 深度提取")
    print("=" * 60)
    
    top_articles = state.get("top_articles", [])
    candidate_pool = state.get("candidate_pool", [])
    
    # 1. 数据验证
    if not top_articles:
        print("✗ top_articles 为空，无需提取")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] deep_extraction_node: top_articles 为空")
        return state
    
    print(f"\n[1/4] 开始深度提取 {len(top_articles)} 条 Top 新闻...")
    
    # 2. 并发抓取正文
    print(f"\n[2/4] 并发抓取正文 (并发数: 5)...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        extracted_articles = loop.run_until_complete(
            batch_extract_articles(
                articles=top_articles.copy(),
                max_concurrency=5,
                timeout=30
            )
        )
        loop.close()
        
        # 统计提取结果
        success_count = sum(1 for article in extracted_articles if article.get("content") is not None)
        fail_count = len(extracted_articles) - success_count
        
        print(f"✓ 初次提取完成: {success_count} 成功, {fail_count} 失败")
        
    except Exception as e:
        error_msg = f"批量提取失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] deep_extraction_node: {error_msg}")
        return state
    
    # 3. 处理失败项：从 candidate_pool 补齐
    print(f"\n[3/4] 处理提取失败项并补齐...")
    
    final_articles = []
    backup_candidates = candidate_pool[len(top_articles):]  # 第 16 名及以后
    backup_index = 0
    
    for i, article in enumerate(extracted_articles):
        if article.get("content") is not None:
            # 提取成功，保留
            final_articles.append(article)
        else:
            # 提取失败，记录错误
            error_msg = f"正文提取失败 [{article.get('title', 'Unknown')[:40]}...]: {article.get('extraction_error', 'Unknown error')}"
            print(f"  ⚠ {error_msg}")
            state["error_logs"].append(f"[{datetime.now().isoformat()}] deep_extraction_node: {error_msg}")
            
            # 尝试从备份候选池补齐
            while backup_index < len(backup_candidates):
                backup_article = backup_candidates[backup_index].copy()
                backup_index += 1
                
                print(f"    尝试从候选池第 {len(top_articles) + backup_index} 名补齐: {backup_article.get('title', 'Unknown')[:40]}...")
                
                # 单独提取备份文章
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    from src.extraction import extract_article_content
                    backup_content = loop.run_until_complete(
                        extract_article_content(backup_article.get("url"), timeout=30)
                    )
                    loop.close()
                    
                    if backup_content:
                        backup_article["content"] = backup_content
                        backup_article["content_length"] = len(backup_content)
                        backup_article["extraction_error"] = None
                        backup_article["is_backup"] = True  # 标记为补齐项
                        backup_article["backup_for_index"] = i  # 记录补齐位置
                        final_articles.append(backup_article)
                        print(f"    ✓ 补齐成功")
                        break
                    else:
                        error_msg = f"补齐候选提取失败: {backup_article.get('title', 'Unknown')[:40]}..."
                        print(f"    ✗ {error_msg}")
                        state["error_logs"].append(f"[{datetime.now().isoformat()}] deep_extraction_node: {error_msg}")
                        
                except Exception as e:
                    error_msg = f"补齐候选提取异常: {str(e)}"
                    print(f"    ✗ {error_msg}")
                    state["error_logs"].append(f"[{datetime.now().isoformat()}] deep_extraction_node: {error_msg}")
            else:
                # 没有更多备份可用
                error_msg = f"无法为第 {i+1} 条新闻找到可用补齐候选"
                print(f"  ✗ {error_msg}")
                state["error_logs"].append(f"[{datetime.now().isoformat()}] deep_extraction_node: {error_msg}")
    
    # 4. 更新状态
    print(f"\n[4/4] 更新状态...")
    state["top_articles"] = final_articles
    
    # 统计信息
    backup_count = sum(1 for article in final_articles if article.get("is_backup"))
    total_content_length = sum(article.get("content_length", 0) for article in final_articles)
    
    print(f"✓ 深度提取完成")
    print(f"  - 最终有效文章: {len(final_articles)} 条")
    print(f"  - 原始提取成功: {success_count} 条")
    print(f"  - 从候选池补齐: {backup_count} 条")
    print(f"  - 总内容长度: {total_content_length:,} 字符")
    
    # 显示前 5 条摘要
    print(f"\n  提取结果预览 (前 5 条):")
    for i, article in enumerate(final_articles[:5], 1):
        content_len = article.get("content_length", 0)
        is_backup = "[补齐] " if article.get("is_backup") else ""
        print(f"    {i}. {is_backup}{article.get('title', 'Unknown')[:50]}... ({content_len:,} 字符)")
    
    return state


def summarize_node(state: GraphState) -> GraphState:
    """
    分级摘要生成节点（重构版）

    处理 candidate_pool 中所有文章：
    1. 翻译所有标题
    2. Top 15: 深度摘要
    3. 其余: 精简摘要
    4. 更新 Qdrant

    模型: qwen3-30b-a3b-instruct-2507

    Args:
        state: 当前状态

    Returns:
        更新后的状态，top_articles 和 candidate_pool 包含生成的摘要和翻译标题
    """
    import asyncio
    from src.llm import get_llm_client
    from datetime import datetime

    print("\n" + "=" * 60)
    print("[Node] summarize_node - 分级摘要生成（重构版）")
    print("=" * 60)

    candidate_pool = state.get("candidate_pool", [])

    # 1. 数据验证
    if not candidate_pool:
        print("✗ candidate_pool 为空，无需生成摘要")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] summarize_node: candidate_pool 为空")
        return state

    print(f"\n[1/6] 开始处理 {len(candidate_pool)} 条新闻...")

    # 2. 加载 Prompt 模板
    prompt_dir = os.path.join(os.path.dirname(__file__), "..", "..", "src", "prompt")

    try:
        # 加载深度摘要 Prompt (Top 15)
        deep_prompt_path = os.path.join(prompt_dir, "summary_prompt.md")
        with open(deep_prompt_path, "r", encoding="utf-8") as f:
            deep_prompt_template = f.read()
        print(f"✓ 已加载深度摘要 Prompt (Top 15)")

        # 加载精简摘要 Prompt (其余)
        simple_prompt_path = os.path.join(prompt_dir, "simple_summary_prompt.md")
        with open(simple_prompt_path, "r", encoding="utf-8") as f:
            simple_prompt_template = f.read()
        print(f"✓ 已加载精简摘要 Prompt (其余)")

    except Exception as e:
        error_msg = f"加载 Prompt 失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] summarize_node: {error_msg}")
        return state

    llm_client = get_llm_client()
    model = "qwen3-30b-a3b-instruct-2507"

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 3. 翻译所有标题
        print(f"\n[2/6] 翻译所有标题 ({len(candidate_pool)} 条)...")
        translated_articles = loop.run_until_complete(
            llm_client.batch_translate_titles(
                articles=candidate_pool,
                model="qwen-turbo",
                max_concurrency=5
            )
        )

        translated_count = sum(1 for a in translated_articles if a.get("translation_error") is None)
        error_count = len(translated_articles) - translated_count
        print(f"✓ 标题翻译完成: {translated_count} 成功, {error_count} 失败")

        # 记录翻译错误
        for article in translated_articles:
            if article.get("translation_error"):
                error_msg = f"标题翻译失败 '{article.get('title', 'Unknown')[:40]}...': {article['translation_error']}"
                state["error_logs"].append(f"[{datetime.now().isoformat()}] summarize_node: {error_msg}")

        # 4. 按 final_score 排序
        sorted_articles = sorted(translated_articles, key=lambda x: x.get("final_score", 0), reverse=True)
        print(f"\n[3/6] 按 final_score 排序完成")

        # 5. 分级处理
        # Top 15: 深度摘要
        top_15 = sorted_articles[:15] if len(sorted_articles) >= 15 else sorted_articles
        # 其余: 精简摘要
        rest_articles = sorted_articles[15:] if len(sorted_articles) > 15 else []

        print(f"\n[4/6] 分级策略:")
        print(f"  - Top 15 ({len(top_15)} 条): 生成深度解读")
        print(f"  - 其余 ({len(rest_articles)} 条): 生成精简简报")

        summarized_articles = []

        # 5.1 生成深度摘要 (Top 15)
        if top_15:
            print(f"\n[5/6] 生成深度摘要 (Top 15)...")
            deep_results = loop.run_until_complete(
                llm_client.batch_generate_summaries(
                    articles=top_15,
                    prompt_template=deep_prompt_template,
                    model=model,
                    max_concurrency=5,
                    summary_type="deep"
                )
            )

            deep_success = sum(1 for a in deep_results if a.get("summary_error") is None)
            deep_fail = len(deep_results) - deep_success
            print(f"✓ 深度摘要完成: {deep_success} 成功, {deep_fail} 失败")

            # 记录错误
            for article in deep_results:
                if article.get("summary_error"):
                    error_msg = f"深度摘要生成失败 '{article.get('title', 'Unknown')[:40]}...': {article['summary_error']}"
                    print(f"  ⚠ {error_msg}")
                    state["error_logs"].append(f"[{datetime.now().isoformat()}] summarize_node: {error_msg}")

            summarized_articles.extend(deep_results)

        # 5.2 生成精简摘要 (其余)
        if rest_articles:
            print(f"\n[5/6] 生成精简摘要 (其余 {len(rest_articles)} 条)...")
            simple_results = loop.run_until_complete(
                llm_client.batch_generate_summaries(
                    articles=rest_articles,
                    prompt_template=simple_prompt_template,
                    model=model,
                    max_concurrency=5,
                    summary_type="simple"
                )
            )

            simple_success = sum(1 for a in simple_results if a.get("summary_error") is None)
            simple_fail = len(simple_results) - simple_success
            print(f"✓ 精简摘要完成: {simple_success} 成功, {simple_fail} 失败")

            # 记录错误
            for article in simple_results:
                if article.get("summary_error"):
                    error_msg = f"精简摘要生成失败 '{article.get('title', 'Unknown')[:40]}...': {article['summary_error']}"
                    print(f"  ⚠ {error_msg}")
                    state["error_logs"].append(f"[{datetime.now().isoformat()}] summarize_node: {error_msg}")

            summarized_articles.extend(simple_results)

        loop.close()

    except Exception as e:
        error_msg = f"批量生成摘要失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] summarize_node: {error_msg}")
        return state

    # 6. 更新 Qdrant
    print(f"\n[6/6] 更新 Qdrant...")
    vector_store = get_vector_store()
    updated_count = 0

    for article in summarized_articles:
        try:
            success = vector_store.update_news_fields(
                news_id=str(article.get("id")),
                fields={
                    "translated_title": article.get("translated_title"),
                    "generated_summary": article.get("generated_summary"),
                    "summary_type": article.get("summary_type")
                }
            )
            if success:
                updated_count += 1
        except Exception as e:
            error_msg = f"更新 Qdrant 失败 '{article.get('title', 'Unknown')[:40]}...': {str(e)}"
            print(f"  ⚠ {error_msg}")
            state["error_logs"].append(f"[{datetime.now().isoformat()}] summarize_node: {error_msg}")

    print(f"✓ Qdrant 更新完成: {updated_count}/{len(summarized_articles)} 条")

    # 7. 更新状态
    state["candidate_pool"] = summarized_articles
    # Top 25 用于 delivery
    state["top_articles"] = summarized_articles[:25] if len(summarized_articles) >= 25 else summarized_articles

    # 统计信息
    total_success = sum(1 for a in summarized_articles if a.get("summary_error") is None)
    total_fail = len(summarized_articles) - total_success
    deep_count = sum(1 for a in summarized_articles if a.get("summary_type") == "deep")
    simple_count = sum(1 for a in summarized_articles if a.get("summary_type") == "simple")

    print(f"\n✓ 摘要生成完成")
    print(f"  - 总计: {len(summarized_articles)} 条")
    print(f"  - 成功: {total_success} 条")
    print(f"  - 失败: {total_fail} 条")
    print(f"  - 深度解读 (Top 15): {deep_count} 条")
    print(f"  - 精简简报 (其余): {simple_count} 条")

    # 显示前 3 条摘要预览
    print(f"\n  摘要预览 (前 3 条):")
    for i, article in enumerate(summarized_articles[:3], 1):
        summary_type = "[深度]" if article.get("summary_type") == "deep" else "[精简]"
        title_display = article.get("translated_title") or article.get("title", "Unknown")
        summary_preview = article.get("generated_summary", "")[:60] if article.get("generated_summary") else "生成失败"
        print(f"    {i}. {summary_type} {title_display[:40]}...")
        print(f"       摘要: {summary_preview}...")

    return state


def delivery_node(state: GraphState) -> GraphState:
    """
    邮件交付节点（简化版）

    使用 Jinja2 组装 HTML 邮件：
    - 头部: 今日科技趋势概览
    - 主体: 10 条深度解读 + 15 条精简简报
    - 底部: 抓取失败的错误日志（HTML 注释形式隐藏）

    标题翻译已在 summarize_node 完成，直接使用已翻译的标题。

    通过 SMTP 发送至指定邮箱

    Args:
        state: 当前状态

    Returns:
        更新后的状态，final_email 包含最终 HTML
    """
    from jinja2 import Template
    from datetime import datetime
    from src.email_sender import get_email_sender

    print("\n" + "=" * 60)
    print("[Node] delivery_node - 邮件交付")
    print("=" * 60)

    top_articles = state.get("top_articles", [])
    error_logs = state.get("error_logs", [])

    # 1. 数据验证
    if not top_articles:
        print("✗ top_articles 为空，无法生成邮件")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] delivery_node: top_articles 为空")
        return state

    print(f"\n[1/3] 准备生成邮件，共 {len(top_articles)} 条新闻...")

    # 2. 加载邮件模板
    try:
        template_path = os.path.join(os.path.dirname(__file__), "..", "..", "src", "prompt", "email_template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
        template = Template(template_content)
        print(f"✓ 已加载邮件模板")
    except Exception as e:
        error_msg = f"加载邮件模板失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] delivery_node: {error_msg}")
        return state

    # 3. 准备模板数据（直接使用已翻译的标题）
    print(f"\n[2/3] 准备邮件数据...")

    # 分离深度解读和精简简报
    deep_articles = []
    simple_articles = []

    for i, article in enumerate(top_articles):
        # 使用已翻译的标题，如果翻译失败则使用原标题
        display_title = article.get("translated_title") or article.get("title", "无标题")

        article_data = {
            "rank": i + 1,
            "title": display_title,
            "url": article.get("url", "#"),
            "source": article.get("source", "未知来源"),
            "category": article.get("category", "其他"),
            "score": article.get("score", 0),
            "llm_score": article.get("llm_score", 0),
            "summary": article.get("generated_summary", "暂无摘要")
        }

        if i < 10:
            deep_articles.append(article_data)
        else:
            simple_articles.append(article_data)

    print(f"  - 深度解读: {len(deep_articles)} 条")
    print(f"  - 精简简报: {len(simple_articles)} 条")

    # 获取当前日期和星期
    now = datetime.now()
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekdays[now.weekday()]

    template_data = {
        "date": now.strftime("%Y年%m月%d日"),
        "weekday": weekday,
        "total_count": len(top_articles),
        "deep_count": len(deep_articles),
        "simple_count": len(simple_articles),
        "deep_articles": deep_articles,
        "simple_articles": simple_articles,
        "generation_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "error_count": len(error_logs),
        "error_logs": error_logs
    }

    # 4. 渲染 HTML
    print(f"\n[3/3] 渲染 HTML 邮件...")
    try:
        html_content = template.render(**template_data)
        state["final_email"] = html_content
        print(f"✓ HTML 渲染完成，邮件大小: {len(html_content):,} 字符")
    except Exception as e:
        error_msg = f"渲染 HTML 失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] delivery_node: {error_msg}")
        return state

    # 5. 发送邮件
    try:
        # 获取收件人邮箱（从环境变量读取，默认使用发件人邮箱）
        recipient = os.getenv("NEWSLETTER_RECIPIENT", os.getenv("SMTP_USER"))

        if not recipient:
            print(f"⚠ 未配置收件人邮箱 (NEWSLETTER_RECIPIENT)，跳过邮件发送")
            print(f"  邮件内容已保存到 state['final_email']")
        else:
            email_sender = get_email_sender()
            success = email_sender.send_newsletter(
                to_email=recipient,
                html_content=html_content,
                date_str=now.strftime("%Y年%m月%d日")
            )

            if success:
                print(f"✓ 邮件发送成功到: {recipient}")
            else:
                error_msg = f"邮件发送失败"
                print(f"✗ {error_msg}")
                state["error_logs"].append(f"[{datetime.now().isoformat()}] delivery_node: {error_msg}")

    except Exception as e:
        error_msg = f"发送邮件时出错: {str(e)}"
        print(f"✗ {error_msg}")
        state["error_logs"].append(f"[{datetime.now().isoformat()}] delivery_node: {error_msg}")

    # 6. 保存邮件到文件（无论发送成功与否）
    try:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "output")
        os.makedirs(output_dir, exist_ok=True)

        date_str = now.strftime("%Y%m%d")
        email_file = os.path.join(output_dir, f"newsletter_{date_str}.html")

        with open(email_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"\n✓ 邮件已保存到文件: {email_file}")
    except Exception as e:
        print(f"⚠ 保存邮件文件失败: {e}")

    print(f"\n" + "=" * 60)
    print("邮件交付节点完成")
    print(f"  - 深度解读: {len(deep_articles)} 条")
    print(f"  - 精简简报: {len(simple_articles)} 条")
    print(f"  - 错误日志: {len(error_logs)} 条")
    print("=" * 60)

    return state


# 节点映射表，用于 workflow 构建
NODE_FUNCTIONS = {
    "fetch_data": fetch_data_node,
    "scoring": scoring_node,
    "deep_extraction": deep_extraction_node,
    "summarize": summarize_node,
    "delivery": delivery_node,
}
