"""
语义去重模块
实现设计文档 2.2 节的语义去重功能：
1. 将数据转为 Markdown 格式
2. 调用 Qwen Embedding 接口将 Markdown 内容向量化
3. 在 Qdrant 中检索相似度 > 0.9 的记录
4. 若重复，更新 Metadata.score（累加权重），不再新增记录
5. 持久化存入 Qdrant，Metadata 包含 score, source, url, timestamp
"""

import sys
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.embeddings import get_embedding_client, EmbeddingClient
from src.vector_store import get_vector_store, VectorStore


def format_to_markdown(article: Dict[str, Any]) -> str:
    """
    将单条文章数据格式化为 Markdown 格式
    
    格式：
    # {Title}
    - Source: {Source}
    - Link: {URL}
    - Raw_Summary: {Summary/Tagline}
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


class SemanticDeduplicator:
    """语义去重器"""
    
    def __init__(
        self,
        embedding_client: EmbeddingClient = None,
        vector_store: VectorStore = None,
        similarity_threshold: float = 0.9
    ):
        """
        初始化语义去重器
        
        Args:
            embedding_client: Embedding 客户端
            vector_store: 向量存储客户端
            similarity_threshold: 相似度阈值，默认 0.9
        """
        self.embedding_client = embedding_client or get_embedding_client()
        self.vector_store = vector_store or get_vector_store()
        self.similarity_threshold = similarity_threshold
        
    def process_news_batch(
        self,
        news_list: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量处理新闻，进行语义去重
        
        Args:
            news_list: 新闻列表，每项包含 title, url, source, score, raw_summary, timestamp
            
        Returns:
            (新插入的记录列表, 更新的记录列表)
        """
        if not news_list:
            return [], []
        
        print(f"\n开始处理 {len(news_list)} 条新闻...")
        
        # 1. 将所有文章转为 Markdown 格式
        print(f"[1/4] 正在转换为 Markdown 格式...")
        markdown_contents = []
        for news in news_list:
            markdown = format_to_markdown(news)
            markdown_contents.append(markdown)
        print(f"✓ 成功转换 {len(markdown_contents)} 条 Markdown")
        
        # 2. 调用 Embedding API 将 Markdown 向量化
        print(f"[2/4] 正在生成 Embedding...")
        try:
            vectors = self.embedding_client.embed_documents(markdown_contents)
            print(f"✓ 成功生成 {len(vectors)} 个向量")
        except Exception as e:
            print(f"✗ Embedding 生成失败: {e}")
            raise
        
        # 3. 逐个检查并处理
        print(f"[3/4] 正在检查重复...")
        new_records = []
        updated_records = []
        
        for i, (news, vector) in enumerate(zip(news_list, vectors)):
            result = self._process_single_news(news, vector)
            if result["action"] == "insert":
                new_records.append(result["data"])
            else:
                updated_records.append(result["data"])
            
            if (i + 1) % 10 == 0:
                print(f"  已处理 {i + 1}/{len(news_list)} 条")
        
        print(f"[4/4] 处理完成")
        print(f"  - 新插入: {len(new_records)} 条")
        print(f"  - 更新: {len(updated_records)} 条")
        
        return new_records, updated_records
    
    def _process_single_news(
        self,
        news: Dict[str, Any],
        vector: List[float]
    ) -> Dict[str, Any]:
        """
        处理单条新闻
        
        Args:
            news: 新闻数据
            vector: Markdown 内容向量
            
        Returns:
            处理结果，包含 action 和 data
        """
        # 生成唯一 ID（基于 URL）
        news_id = self._generate_id(news["url"])
        
        # 检查是否已存在相似记录
        duplicate = self.vector_store.check_duplicate(
            vector,
            threshold=self.similarity_threshold
        )
        
        if duplicate:
            # 重复：更新 score（累加权重）
            existing_score = duplicate["payload"].get("score", 0)
            new_score = existing_score + news.get("score", 0)
            
            self.vector_store.client.set_payload(
                collection_name=self.vector_store.collection_name,
                payload={"score": new_score},
                points=[duplicate["id"]]
            )
            
            return {
                "action": "update",
                "data": {
                    "id": duplicate["id"],
                    "old_score": existing_score,
                    "new_score": new_score,
                    "title": duplicate["payload"].get("title", ""),
                    "similarity": duplicate["score"]
                }
            }
        else:
            self.vector_store.upsert_news(
                news_id=news_id,
                vector=vector,
                title=news["title"],
                url=news["url"],
                source=news.get("source", "Unknown"),
                score=news.get("score", 0),
                raw_summary=news.get("raw_summary", ""),
                content=news.get("content", ""),
                timestamp=news.get("timestamp", datetime.now().isoformat())
            )
            
            return {
                "action": "insert",
                "data": {
                    "id": news_id,
                    "title": news["title"],
                    "score": news.get("score", 0)
                }
            }
    
    def _generate_id(self, url: str) -> str:
        """基于 URL 生成唯一 ID"""
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()


def process_and_deduplicate(
    news_list: List[Dict[str, Any]],
    similarity_threshold: float = 0.9
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    便捷函数：处理新闻列表并进行语义去重
    
    Args:
        news_list: 新闻列表
        similarity_threshold: 相似度阈值
        
    Returns:
        (新插入的记录列表, 更新的记录列表)
    """
    deduplicator = SemanticDeduplicator(similarity_threshold=similarity_threshold)
    return deduplicator.process_news_batch(news_list)


if __name__ == "__main__":
    print("=" * 60)
    print("语义去重功能测试")
    print("=" * 60)
    
    # 测试数据
    test_news = [
        {
            "title": "OpenAI 发布 GPT-5，性能提升显著",
            "url": "https://example.com/openai-gpt5",
            "source": "Tech News",
            "score": 100,
            "raw_summary": "OpenAI 最新模型发布",
            "timestamp": datetime.now().isoformat()
        },
        {
            "title": "OpenAI 发布 GPT-5，性能大幅提升",  # 相似标题
            "url": "https://example.com/openai-gpt5-v2",
            "source": "AI Daily",
            "score": 80,
            "raw_summary": "GPT-5 正式发布",
            "timestamp": datetime.now().isoformat()
        },
        {
            "title": "Google 推出新的 AI 芯片",
            "url": "https://example.com/google-ai-chip",
            "source": "TechCrunch",
            "score": 90,
            "raw_summary": "Google 新芯片发布",
            "timestamp": datetime.now().isoformat()
        },
        {
            "title": "微软发布 Windows 12",
            "url": "https://example.com/windows-12",
            "source": "The Verge",
            "score": 85,
            "raw_summary": "Windows 12 来了",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    print(f"\n测试数据: {len(test_news)} 条新闻")
    print("\n新闻标题:")
    for i, news in enumerate(test_news, 1):
        print(f"  {i}. {news['title']} (score: {news['score']})")
    
    try:
        # 创建去重器
        deduplicator = SemanticDeduplicator()
        
        # 确保集合存在
        print("\n[初始化] 检查 Qdrant 集合...")
        deduplicator.vector_store.create_collection()
        
        # 处理新闻
        print("\n[处理] 开始语义去重...")
        new_records, updated_records = deduplicator.process_news_batch(test_news)
        
        # 再次处理相同数据，测试去重效果
        print("\n" + "=" * 60)
        print("再次处理相同数据（测试去重效果）")
        print("=" * 60)
        new_records2, updated_records2 = deduplicator.process_news_batch(test_news)
        
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        print(f"第一次处理:")
        print(f"  - 新插入: {len(new_records)} 条")
        print(f"  - 更新: {len(updated_records)} 条")
        print(f"第二次处理（去重）:")
        print(f"  - 新插入: {len(new_records2)} 条")
        print(f"  - 更新: {len(updated_records2)} 条")
        print(f"\n✓ 测试完成！")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
