"""
Qdrant 向量数据库模块
用于存储新闻标题的向量表示，实现语义去重功能
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition
from dotenv import load_dotenv

load_dotenv()


class VectorStore:
    """Qdrant 向量存储封装类"""
    
    def __init__(
        self,
        url: Optional[str] = None,
        collection_name: Optional[str] = None,
        vector_size: int = 1024
    ):
        """
        初始化 Qdrant 连接
        
        Args:
            url: Qdrant 服务 URL，默认从环境变量 QDRANT_URL 获取
            collection_name: 集合名称，默认从环境变量 QDRANT_COLLECTION_NAME 获取
            vector_size: 向量维度，默认 1024 (text-embedding-v4 维度)
        """
        self.url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "tech_news")
        self.vector_size = vector_size
        self.client = QdrantClient(url=self.url)
        
    def create_collection(self, recreate: bool = False) -> bool:
        """
        创建集合
        
        Args:
            recreate: 如果集合已存在，是否重新创建
            
        Returns:
            bool: 创建成功返回 True
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name in collection_names:
                if recreate:
                    self.client.delete_collection(self.collection_name)
                    print(f"已删除旧集合: {self.collection_name}")
                else:
                    print(f"集合已存在: {self.collection_name}")
                    return True
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"成功创建集合: {self.collection_name}")
            return True
            
        except Exception as e:
            print(f"创建集合失败: {e}")
            return False
    
    def check_duplicate(
        self,
        vector: List[float],
        threshold: float = 0.9
    ) -> Optional[Dict[str, Any]]:
        """
        检查是否存在相似向量（语义去重）
        
        Args:
            vector: 待检查的向量
            threshold: 相似度阈值，默认 0.9
            
        Returns:
            如果存在相似记录，返回该记录信息；否则返回 None
        """
        try:
            from qdrant_client.models import SearchRequest, Filter
            
            # 使用 query_points 方法进行向量搜索
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=vector,
                limit=1,
                score_threshold=threshold,
                with_payload=True,
                with_vectors=False
            )
            
            if results and results.points:
                result = results.points[0]
                return {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                }
            return None
            
        except Exception as e:
            print(f"检查重复失败: {e}")
            return None
    
    def upsert_news(
        self,
        news_id: str,
        vector: List[float],
        title: str,
        url: str,
        source: str,
        score: float,
        raw_summary: str,
        content: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        插入或更新新闻记录
        
        Args:
            news_id: 新闻唯一标识
            vector: 标题的向量表示
            title: 新闻标题
            url: 新闻链接
            source: 数据来源
            score: 热度分数
            raw_summary: 原始摘要
            content: 正文内容
            timestamp: 时间戳
            
        Returns:
            bool: 操作成功返回 True
        """
        try:
            duplicate = self.check_duplicate(vector)
            
            if duplicate:
                existing_score = duplicate["payload"].get("score", 0)
                new_score = existing_score + score
                
                now = datetime.now().isoformat()
                updated_point = PointStruct(
                    id=duplicate["id"],
                    vector=vector,
                    payload={
                        **duplicate["payload"],
                        "score": new_score,
                        "updated_at": now
                    }
                )
                
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[updated_point]
                )
                print(f"更新记录 score: {existing_score} -> {new_score} (URL: {url})")
                return True
            
            now = datetime.now().isoformat()
            point = PointStruct(
                id=news_id,
                vector=vector,
                payload={
                    "title": title,
                    "url": url,
                    "source": source,
                    "score": score,
                    "raw_summary": raw_summary,
                    "content": content or "",
                    "timestamp": timestamp or now,
                    "inserted_at": now
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            print(f"插入新记录: {title[:50]}...")
            return True
            
        except Exception as e:
            print(f"插入记录失败: {e}")
            return False
    
    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """获取集合信息"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vector_size": self.vector_size,
                "points_count": info.points_count,
                "status": str(info.status)
            }
        except Exception as e:
            print(f"获取集合信息失败: {e}")
            return None
    
    def test_connection(self) -> bool:
        """测试 Qdrant 连接"""
        try:
            collections = self.client.get_collections()
            print(f"✓ 成功连接到 Qdrant")
            print(f"  URL: {self.url}")
            print(f"  现有集合数: {len(collections.collections)}")
            return True
        except Exception as e:
            print(f"✗ 连接 Qdrant 失败: {e}")
            return False
    
    def fetch_today_news(
        self,
        date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取当日插入的新闻元数据
        
        按 inserted_at 字段过滤，范围为 UTC+8 时间当日 00:00:00 至 23:59:59
        
        Args:
            date: 指定日期，默认为今天
            
        Returns:
            当日新闻记录列表，每项包含完整的 payload 数据
        """
        try:
            # 确定查询日期（默认为今天）
            if date is None:
                # 获取当前 UTC+8 时间
                date = datetime.utcnow() + timedelta(hours=8)
            
            # 构建当日日期字符串（UTC+8）
            date_str = date.strftime("%Y-%m-%d")
            
            print(f"查询日期 (UTC+8): {date_str}")
            
            # 由于 inserted_at 是 ISO 格式字符串，我们使用前缀匹配
            # 获取所有记录后在内存中过滤
            results = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # 设置足够大的限制
                with_payload=True,
                with_vectors=False
            )
            
            # 提取记录并过滤
            records = []
            if results and results[0]:
                for point in results[0]:
                    payload = point.payload
                    inserted_at = payload.get("inserted_at", "")
                    
                    # 检查 inserted_at 是否以当日日期开头
                    if inserted_at and inserted_at.startswith(date_str):
                        record = {
                            "id": point.id,
                            **payload
                        }
                        records.append(record)
            
            print(f"✓ 查询完成，找到 {len(records)} 条当日记录")
            return records
            
        except Exception as e:
            print(f"✗ 查询当日新闻失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def update_news_fields(self, news_id: str, fields: Dict[str, Any]) -> bool:
        """
        更新新闻记录的指定字段

        Args:
            news_id: 新闻唯一标识
            fields: 要更新的字段字典

        Returns:
            bool: 操作成功返回 True
        """
        try:
            # 先获取现有记录
            existing_record = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[news_id],
                with_payload=True,
                with_vectors=True
            )

            if not existing_record:
                print(f"记录不存在: {news_id}")
                return False

            # 获取现有向量和 payload
            point = existing_record[0]
            existing_vector = point.vector
            existing_payload = point.payload or {}

            # 合并新字段
            updated_payload = {**existing_payload, **fields}
            updated_payload["updated_at"] = datetime.now().isoformat()

            # 创建更新后的点
            updated_point = PointStruct(
                id=news_id,
                vector=existing_vector if existing_vector else [0.0] * self.vector_size,
                payload=updated_payload
            )

            # 更新记录
            self.client.upsert(
                collection_name=self.collection_name,
                points=[updated_point]
            )
            return True

        except Exception as e:
            print(f"更新记录失败: {e}")
            return False

    def batch_update_news_fields(self, updates: List[Dict[str, Any]]) -> int:
        """
        批量更新新闻记录的指定字段

        Args:
            updates: 更新列表，每项包含 id 和 fields

        Returns:
            int: 成功更新的记录数
        """
        success_count = 0

        for update in updates:
            news_id = update.get("id")
            fields = update.get("fields", {})

            if news_id and fields:
                if self.update_news_fields(str(news_id), fields):
                    success_count += 1

        return success_count

    def fetch_news_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        获取指定日期范围内的新闻元数据
        
        Args:
            start_date: 开始时间（UTC+8）
            end_date: 结束时间（UTC+8）
            
        Returns:
            新闻记录列表
        """
        try:
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()
            
            # 获取所有记录后在内存中过滤
            results = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            records = []
            if results and results[0]:
                for point in results[0]:
                    payload = point.payload
                    inserted_at = payload.get("inserted_at", "")
                    
                    # 字符串比较（ISO 格式字符串可以按字典序比较）
                    if inserted_at and start_str <= inserted_at <= end_str:
                        records.append({
                            "id": point.id,
                            **payload
                        })
            
            return records
            
        except Exception as e:
            print(f"查询日期范围失败: {e}")
            return []


# 便捷函数
def get_vector_store() -> VectorStore:
    """获取默认配置的 VectorStore 实例"""
    return VectorStore()


if __name__ == "__main__":
    print("=" * 60)
    print("Qdrant 向量存储测试")
    print("=" * 60)
    
    # 创建 VectorStore 实例
    store = get_vector_store()
    
    # 测试连接
    print("\n[1/3] 测试连接...")
    if not store.test_connection():
        print("\n请确保 Qdrant 服务已启动:")
        print("  docker-compose up -d qdrant")
        exit(1)
    
    # 创建集合
    print("\n[2/3] 创建集合...")
    store.create_collection()
    
    # 获取集合信息
    print("\n[3/3] 集合信息:")
    info = store.get_collection_info()
    if info:
        print(f"  集合名称: {store.collection_name}")
        print(f"  向量维度: {store.vector_size}")
        print(f"  记录数量: {info.get('points_count', 0)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
