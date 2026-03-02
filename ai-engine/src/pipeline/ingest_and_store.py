"""
完整数据获取和持久化流程

1. 从 RSS Feeds 获取数据
2. 使用语义去重处理数据
3. 将去重后的数据持久化到 Qdrant
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.ingestion.rss_feeds import fetch_rss_feeds_parallel
from src.preprocessing.semantic_dedup import SemanticDeduplicator
from src.vector_store import get_vector_store


def fetch_all_data() -> List[Dict]:
    """
    从 RSS Feeds 获取数据
    
    Returns:
        RSS Feeds 文章列表
    """
    print("\n" + "=" * 60)
    print("开始获取数据...")
    print("=" * 60)
    
    print("\n[1/1] 正在获取 RSS Feeds 数据...")
    try:
        rss_feeds_data = fetch_rss_feeds_parallel()
        print(f"✓ 获取到 {len(rss_feeds_data)} 条 RSS 文章")
    except Exception as e:
        print(f"✗ 获取 RSS Feeds 数据失败: {e}")
        rss_feeds_data = []
    
    print("\n" + "=" * 60)
    print(f"数据获取完成！总计: {len(rss_feeds_data)} 条文章")
    print("=" * 60)
    
    return rss_feeds_data


def merge_all_articles(rss_feeds_data: List[Dict]) -> List[Dict]:
    """
    处理 RSS Feeds 数据
    
    Args:
        rss_feeds_data: RSS Feeds 数据
        
    Returns:
        处理后的文章列表
    """
    all_articles = []
    
    for article in rss_feeds_data:
        all_articles.append({
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "source": article.get("source", "RSS"),
            "score": article.get("score", 0),
            "raw_summary": article.get("raw_summary", ""),
            "content": article.get("content", ""),
            "timestamp": article.get("timestamp", datetime.now().isoformat())
        })
    
    return all_articles


def process_and_store(
    articles: List[Dict],
    clear_collection: bool = True
) -> Dict[str, Any]:
    """
    处理文章并进行语义去重后存储到 Qdrant
    
    Args:
        articles: 文章列表
        clear_collection: 是否清空集合
        
    Returns:
        处理统计信息
    """
    print("\n" + "=" * 60)
    print("开始语义去重和持久化...")
    print("=" * 60)
    
    deduplicator = SemanticDeduplicator()
    
    print("\n[初始化] 检查 Qdrant 集合...")
    if clear_collection:
        print("  清空集合并重新创建...")
        deduplicator.vector_store.create_collection(recreate=True)
    else:
        deduplicator.vector_store.create_collection()
    
    print(f"\n[处理] 正在处理 {len(articles)} 条文章...")
    new_records, updated_records = deduplicator.process_news_batch(articles)
    
    collection_info = deduplicator.vector_store.get_collection_info()
    
    return {
        "total_input": len(articles),
        "new_inserted": len(new_records),
        "updated": len(updated_records),
        "total_stored": collection_info.get("points_count", 0) if collection_info else 0
    }


def verify_stored_data():
    """验证 Qdrant 中存储的数据"""
    print("\n" + "=" * 60)
    print("验证存储的数据...")
    print("=" * 60)
    
    store = get_vector_store()
    info = store.get_collection_info()
    
    if info:
        print(f"\n集合名称: {store.collection_name}")
        print(f"向量维度: {store.vector_size}")
        print(f"记录总数: {info.get('points_count', 0)}")
        
        try:
            results = store.client.scroll(
                collection_name=store.collection_name,
                limit=5,
                with_payload=True,
                with_vectors=False
            )
            
            if results and results[0]:
                print("\n前 5 条记录:")
                for i, point in enumerate(results[0], 1):
                    payload = point.payload
                    print(f"\n  {i}. {payload.get('title', 'N/A')[:60]}...")
                    print(f"     Source: {payload.get('source', 'N/A')}")
                    print(f"     Score: {payload.get('score', 0)}")
                    print(f"     URL: {payload.get('url', 'N/A')[:50]}...")
        except Exception as e:
            print(f"获取记录详情失败: {e}")


def main():
    """主流程"""
    print("=" * 60)
    print("科技新闻数据获取和持久化流程")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    rss_feeds_data = fetch_all_data()
    
    all_articles = merge_all_articles(rss_feeds_data)
    
    if not all_articles:
        print("\n✗ 没有获取到任何数据，流程结束")
        return
    
    print(f"\n合并后总计: {len(all_articles)} 条文章")
    
    stats = process_and_store(all_articles, clear_collection=True)
    
    verify_stored_data()
    
    print("\n" + "=" * 60)
    print("处理统计")
    print("=" * 60)
    print(f"输入文章数: {stats['total_input']}")
    print(f"新插入: {stats['new_inserted']}")
    print(f"更新: {stats['updated']}")
    print(f"Qdrant 总记录数: {stats['total_stored']}")
    print(f"去重率: {(1 - stats['new_inserted'] / stats['total_input']) * 100:.1f}%")
    
    print("\n" + "=" * 60)
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("✓ 流程完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
