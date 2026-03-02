"""
数据预处理与向量化模块

将来自不同数据源（Hacker News、Product Hunt、RSS Feeds）的数据
统一格式化为 Markdown 格式，并进行去重和排序。
"""

from typing import List, Dict, Any
from collections import OrderedDict


def format_to_markdown(article: Dict[str, Any]) -> str:
    """
    将单条文章数据格式化为 Markdown 格式
    
    格式：
    # {Title}
    - Source: {Source}
    - Link: {URL}
    - Raw_Summary: {Summary/Tagline}
    
    Args:
        article: 包含文章信息的字典，必须包含 title, url, source, raw_summary 字段
        
    Returns:
        str: Markdown 格式的字符串
        
    Example:
        >>> article = {
        ...     "title": "Example Article",
        ...     "url": "https://example.com",
        ...     "source": "Hacker News",
        ...     "raw_summary": "This is a summary"
        ... }
        >>> print(format_to_markdown(article))
        # Example Article
        - Source: Hacker News
        - Link: https://example.com
        - Raw_Summary: This is a summary
    """
    title = article.get("title", "")
    url = article.get("url", "")
    source = article.get("source", "")
    raw_summary = article.get("raw_summary", "")
    
    markdown = f"# {title}\n"
    markdown += f"- Source: {source}\n"
    markdown += f"- Link: {url}\n"
    markdown += f"- Raw_Summary: {raw_summary}\n"
    
    return markdown


def batch_format_to_markdown(articles: List[Dict[str, Any]], 
                             separator: str = "\n---\n") -> str:
    """
    批量将文章数据格式化为 Markdown 格式
    
    Args:
        articles: 文章字典列表
        separator: 文章之间的分隔符，默认为 "\n---\n"
        
    Returns:
        str: 包含所有文章的 Markdown 格式字符串
    """
    if not articles:
        return ""
    
    markdown_parts = []
    for article in articles:
        markdown_parts.append(format_to_markdown(article))
    
    return separator.join(markdown_parts)


def merge_all_sources(*sources: List[Dict[str, Any]], 
                     remove_duplicates: bool = True,
                     sort_by_score: bool = True) -> List[Dict[str, Any]]:
    """
    合并多个数据源的文章，并进行去重和排序
    
    Args:
        *sources: 多个文章列表，每个列表来自不同的数据源
        remove_duplicates: 是否基于 URL 去重，默认 True
        sort_by_score: 是否按评分降序排序，默认 True
        
    Returns:
        List[Dict[str, Any]]: 合并后的文章列表
        
    Note:
        去重逻辑：基于 URL 进行去重，保留评分最高的版本
    """
    # 合并所有数据源
    all_articles = []
    for source_list in sources:
        if source_list:
            all_articles.extend(source_list)
    
    # 去重处理
    if remove_duplicates:
        # 使用 OrderedDict 保持顺序，同时基于 URL 去重
        # 保留评分最高的版本
        url_to_article = {}
        for article in all_articles:
            url = article.get("url", "")
            if not url:
                continue
                
            if url in url_to_article:
                # 保留评分更高的版本
                existing_score = url_to_article[url].get("score", 0)
                new_score = article.get("score", 0)
                if new_score > existing_score:
                    url_to_article[url] = article
            else:
                url_to_article[url] = article
        
        all_articles = list(url_to_article.values())
    
    # 排序处理
    if sort_by_score:
        # 按评分降序排序，评分相同的按时间戳降序
        all_articles.sort(key=lambda x: (x.get("score", 0), x.get("timestamp", 0)), 
                         reverse=True)
    
    return all_articles


def preprocess_all_data(hacker_news_data: List[Dict[str, Any]] = None,
                       product_hunt_data: List[Dict[str, Any]] = None,
                       rss_feeds_data: List[Dict[str, Any]] = None,
                       output_format: str = "markdown") -> str:
    """
    预处理所有数据源的数据，输出统一格式的结果
    
    Args:
        hacker_news_data: Hacker News 数据
        product_hunt_data: Product Hunt 数据
        rss_feeds_data: RSS Feeds 数据
        output_format: 输出格式，目前仅支持 "markdown"
        
    Returns:
        str: 格式化后的字符串
        
    Example:
        >>> result = preprocess_all_data(
        ...     hacker_news_data=[{"title": "HN Article", ...}],
        ...     product_hunt_data=[{"title": "PH Product", ...}],
        ...     rss_feeds_data=[{"title": "RSS Article", ...}]
        ... )
        >>> print(result)
        # HN Article
        ...
        ---
        # PH Product
        ...
    """
    # 合并所有数据源
    merged_articles = merge_all_sources(
        hacker_news_data or [],
        product_hunt_data or [],
        rss_feeds_data or []
    )
    
    # 根据输出格式返回结果
    if output_format == "markdown":
        return batch_format_to_markdown(merged_articles)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


if __name__ == "__main__":
    import sys
    import os
    # 添加项目根目录到路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # 导入真实数据获取函数
    from src.ingestion.hacker_news import fetch_top_stories
    from src.ingestion.product_hunt import fetch_product_hunt_data
    from src.ingestion.rss_feeds import fetch_rss_feeds_parallel
    
    print("=" * 60)
    print("开始获取真实数据...")
    print("=" * 60)
    
    # 获取 Hacker News 数据
    print("\n[1/3] 正在获取 Hacker News 数据...")
    try:
        hacker_news_data = fetch_top_stories()
        print(f"✓ 获取到 {len(hacker_news_data)} 条 Hacker News 文章")
    except Exception as e:
        print(f"✗ 获取 Hacker News 数据失败: {e}")
        hacker_news_data = []
    
    # 获取 Product Hunt 数据
    print("\n[2/3] 正在获取 Product Hunt 数据...")
    try:
        product_hunt_data = fetch_product_hunt_data()
        print(f"✓ 获取到 {len(product_hunt_data)} 条 Product Hunt 文章")
    except Exception as e:
        print(f"✗ 获取 Product Hunt 数据失败: {e}")
        product_hunt_data = []
    
    # 获取 RSS Feeds 数据
    print("\n[3/3] 正在获取 RSS Feeds 数据...")
    try:
        rss_feeds_data = fetch_rss_feeds_parallel()
        print(f"✓ 获取到 {len(rss_feeds_data)} 条 RSS 文章")
    except Exception as e:
        print(f"✗ 获取 RSS Feeds 数据失败: {e}")
        rss_feeds_data = []
    
    # 统计总数
    total_articles = len(hacker_news_data) + len(product_hunt_data) + len(rss_feeds_data)
    print("\n" + "=" * 60)
    print(f"数据获取完成！总计: {total_articles} 条文章")
    print("=" * 60)
    
    # 处理并输出 Markdown
    print("\n正在生成 Markdown 格式输出...\n")
    print("=" * 60)
    print("MARKDOWN 输出")
    print("=" * 60)
    print()
    
    result = preprocess_all_data(
        hacker_news_data=hacker_news_data,
        product_hunt_data=product_hunt_data,
        rss_feeds_data=rss_feeds_data
    )
    
    print(result)
