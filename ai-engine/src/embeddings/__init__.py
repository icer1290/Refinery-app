"""
Embedding 模块
调用阿里云百炼 text-embedding-v4 API 将文本转换为向量
使用 OpenAI 兼容接口
"""

import os
import hashlib
from typing import List, Union, Optional
from dotenv import load_dotenv

load_dotenv()

# 尝试导入 openai，如果失败则使用模拟模式
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class EmbeddingClient:
    """阿里云百炼 Embedding API 客户端 (OpenAI 兼容模式)"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        mock: bool = False
    ):
        """
        初始化 Embedding 客户端
        
        Args:
            api_key: 阿里云 API Key，默认从环境变量 QWEN_API_KEY 获取
            model: 模型名称，默认 text-embedding-v4
            base_url: API 基础 URL，默认北京地域
            mock: 是否使用模拟模式（用于测试）
        """
        self.api_key = api_key or os.getenv("QWEN_API_KEY")
        self.model = model or os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v4")
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.mock = mock or os.getenv("EMBEDDING_MOCK", "false").lower() == "true"
        
        if not self.mock:
            if not OPENAI_AVAILABLE:
                raise ImportError("openai 包未安装，请运行: uv pip install openai")
            if not self.api_key:
                raise ValueError("API Key 不能为空，请设置 QWEN_API_KEY 环境变量")
            
            # 初始化 OpenAI 客户端
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """生成模拟的 embedding 向量（用于测试）"""
        # 使用文本的哈希值生成确定性的伪随机向量
        # 这样相同的文本会产生相同的向量，不同的文本产生不同的向量
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # 生成 1536 维的向量
        import random
        random.seed(hash_int)
        vector = [random.uniform(-1, 1) for _ in range(1536)]
        
        # 归一化向量
        import math
        norm = math.sqrt(sum(x * x for x in vector))
        vector = [x / norm for x in vector]
        
        return vector
    
    def embed(
        self,
        texts: Union[str, List[str]],
        encoding_format: str = "float"
    ) -> List[List[float]]:
        """
        将文本转换为向量
        
        Args:
            texts: 单个文本或文本列表
            encoding_format: 编码格式，可选 "float" 或 "base64"
            
        Returns:
            向量列表，每个向量是 1536 维的浮点数数组
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if self.mock:
            # 模拟模式：生成伪随机向量
            return [self._generate_mock_embedding(text) for text in texts]
        
        # 阿里云 Embedding API 限制 batch size 不能超过 10
        batch_size = 10
        all_vectors = []
        
        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # 调用 OpenAI 兼容接口
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    encoding_format=encoding_format
                )
                
                # 提取向量
                batch_vectors = [item.embedding for item in response.data]
                all_vectors.extend(batch_vectors)
            
            return all_vectors
            
        except Exception as e:
            raise RuntimeError(f"Embedding API 调用失败: {e}")
    
    def embed_query(self, query: str) -> List[float]:
        """
        将查询文本转换为向量
        
        Args:
            query: 查询文本
            
        Returns:
            1536 维向量
        """
        results = self.embed(query)
        return results[0] if results else []
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        将文档列表转换为向量
        
        Args:
            documents: 文档文本列表
            
        Returns:
            向量列表
        """
        return self.embed(documents)


# 便捷函数
def get_embedding_client(mock: bool = False) -> EmbeddingClient:
    """获取默认配置的 EmbeddingClient 实例"""
    return EmbeddingClient(mock=mock)


def embed_text(text: str, mock: bool = False) -> List[float]:
    """便捷函数：将单个文本转换为向量"""
    client = get_embedding_client(mock=mock)
    return client.embed_query(text)


def embed_texts(texts: List[str], mock: bool = False) -> List[List[float]]:
    """便捷函数：将多个文本转换为向量"""
    client = get_embedding_client(mock=mock)
    return client.embed_documents(texts)


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Embedding API 测试")
    print("=" * 60)
    
    # 检查是否使用模拟模式
    use_mock = os.getenv("EMBEDDING_MOCK", "false").lower() == "true"
    
    try:
        client = get_embedding_client(mock=use_mock)
        print(f"\n模型: {client.model}")
        print(f"Base URL: {client.base_url}")
        print(f"模拟模式: {client.mock}")
        
        # 测试单条文本
        print("\n[1/2] 测试单条文本...")
        text = "OpenAI 发布 GPT-5，性能提升显著"
        vector = client.embed_query(text)
        print(f"✓ 文本: {text}")
        print(f"✓ 向量维度: {len(vector)}")
        print(f"✓ 前5个值: {[round(x, 4) for x in vector[:5]]}")
        
        # 测试批量文本
        print("\n[2/2] 测试批量文本...")
        texts = [
            "Google 推出新的 AI 芯片",
            "微软发布 Windows 12",
            "苹果 WWDC 大会即将召开",
            "特斯拉自动驾驶技术升级"
        ]
        vectors = client.embed_documents(texts)
        print(f"✓ 输入文本数: {len(texts)}")
        print(f"✓ 输出向量数: {len(vectors)}")
        print(f"✓ 每个向量维度: {len(vectors[0]) if vectors else 0}")
        
        # 测试相似性（模拟模式下相同文本应该产生相同向量）
        print("\n[验证] 测试向量一致性...")
        text1 = "测试文本"
        text2 = "测试文本"
        vec1 = client.embed_query(text1)
        vec2 = client.embed_query(text2)
        
        # 计算余弦相似度
        import math
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        similarity = dot_product  # 向量已归一化
        print(f"相同文本相似度: {similarity:.6f} (应该接近 1.0)")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
        if client.mock:
            print("\n注意: 当前使用模拟模式，向量是伪随机生成的")
            print("如需使用真实 API，请设置有效的 QWEN_API_KEY 并运行:")
            print("  EMBEDDING_MOCK=false python src/embeddings/__init__.py")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        print("\n请检查:")
        print("  1. QWEN_API_KEY 环境变量是否设置")
        print("  2. API Key 是否有效")
        print("  3. 网络连接是否正常")
        print("\n或使用模拟模式测试:")
        print("  EMBEDDING_MOCK=true python src/embeddings/__init__.py")
        sys.exit(1)
