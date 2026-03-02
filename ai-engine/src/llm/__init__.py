"""
LLM 客户端模块
封装 Qwen Chat API 调用，支持批量调用、并发控制和重试机制
"""

import os
import json
import asyncio
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI, RateLimitError, APIError


@dataclass
class ScoringResult:
    """打分结果数据结构"""
    score: float
    reason: str
    category: str


class LLMClient:
    """
    LLM 客户端
    封装 Qwen Chat API 调用，支持指数退避重试
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0
    ):
        """
        初始化 LLM 客户端
        
        Args:
            api_key: API Key，默认从环境变量 QWEN_API_KEY 读取
            model: 模型名称，默认从环境变量 QWEN_CHAT_MODEL 读取
            base_url: API 基础 URL
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
        """
        self.api_key = api_key or os.getenv("QWEN_API_KEY")
        self.model = model or os.getenv("QWEN_CHAT_MODEL", "qwen3-vl-30b-a3b-instruct")
        self.base_url = base_url
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        if not self.api_key:
            raise ValueError("API Key 未设置，请设置 QWEN_API_KEY 环境变量")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url
        )
    
    async def score_news_with_retry(
        self,
        title: str,
        summary: str,
        source: str,
        prompt_template: str
    ) -> ScoringResult:
        """
        对单条新闻进行打分（带重试机制）
        
        Args:
            title: 新闻标题
            summary: 新闻摘要
            source: 新闻来源
            prompt_template: 打分 Prompt 模板
            
        Returns:
            ScoringResult 包含 score, reason, category
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await self._score_news_once(title, summary, source, prompt_template)
            except RateLimitError as e:
                last_error = e
                # 指数退避 + 随机抖动
                delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                print(f"    ⚠ API 限流，等待 {delay:.1f} 秒后重试 ({attempt + 1}/{self.max_retries})...")
                await asyncio.sleep(delay)
            except APIError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    print(f"    ⚠ API 错误，等待 {delay:.1f} 秒后重试 ({attempt + 1}/{self.max_retries})...")
                    await asyncio.sleep(delay)
                else:
                    raise
            except Exception as e:
                # 其他错误不重试，直接抛出
                raise Exception(f"LLM API 调用失败: {str(e)}")
        
        # 重试次数用尽
        raise Exception(f"LLM API 调用失败（已重试 {self.max_retries} 次）: {str(last_error)}")
    
    async def _score_news_once(
        self,
        title: str,
        summary: str,
        source: str,
        prompt_template: str
    ) -> ScoringResult:
        """
        单次打分请求（内部方法）
        """
        # 构建新闻内容
        news_content = f"""# {title}

- Source: {source}
- Raw_Summary: {summary}
"""
        
        # 构建完整 Prompt
        full_prompt = f"{prompt_template}\n\n## News Content\n{news_content}\n\n## Output"
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # 解析 JSON 输出
        result = self._parse_scoring_output(content)
        return result
    
    def _parse_scoring_output(self, content: str) -> ScoringResult:
        """
        解析 LLM 的打分输出
        
        Args:
            content: LLM 返回的文本内容
            
        Returns:
            ScoringResult
        """
        try:
            # 尝试提取 JSON 部分
            content = content.strip()
            
            # 如果包含代码块，提取其中的 JSON
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            # 解析 JSON
            data = json.loads(content)
            
            return ScoringResult(
                score=float(data.get("score", 0)),
                reason=data.get("reason", ""),
                category=data.get("category", "其他")
            )
            
        except json.JSONDecodeError:
            # 如果 JSON 解析失败，尝试从文本中提取分数
            import re
            score_match = re.search(r'["\']?score["\']?\s*[:=]\s*(\d+(?:\.\d+)?)', content)
            if score_match:
                score = float(score_match.group(1))
                return ScoringResult(score=score, reason="解析失败，使用默认提取", category="其他")
            
            return ScoringResult(score=0, reason="解析失败", category="其他")
        
        except Exception as e:
            return ScoringResult(score=0, reason=f"解析错误: {str(e)}", category="其他")
    
    async def batch_score_news(
        self,
        news_list: List[Dict[str, Any]],
        prompt_template: str,
        max_concurrency: int = 5
    ) -> List[Dict[str, Any]]:
        """
        批量对新闻进行打分
        
        Args:
            news_list: 新闻列表，每项包含 title, raw_summary, source
            prompt_template: 打分 Prompt 模板
            max_concurrency: 最大并发数（默认 5，降低以避免限流）
            
        Returns:
            包含打分结果的新闻列表，每项新增 llm_score, reason, category 字段
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def score_with_semaphore(news: Dict[str, Any], index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    # 打印进度
                    if (index + 1) % 10 == 0 or index == 0:
                        print(f"    进度: {index + 1}/{len(news_list)}")
                    
                    result = await self.score_news_with_retry(
                        title=news.get("title", ""),
                        summary=news.get("raw_summary", ""),
                        source=news.get("source", ""),
                        prompt_template=prompt_template
                    )
                    
                    return {
                        **news,
                        "llm_score": result.score,
                        "reason": result.reason,
                        "category": result.category,
                        "scoring_error": None
                    }
                except Exception as e:
                    return {
                        **news,
                        "llm_score": 0,
                        "reason": f"打分失败: {str(e)}",
                        "category": "其他",
                        "scoring_error": str(e)
                    }
        
        # 并发执行所有打分任务
        tasks = [score_with_semaphore(news, i) for i, news in enumerate(news_list)]
        results = await asyncio.gather(*tasks)
        
        return list(results)
    
    async def generate_summary_with_retry(
        self,
        title: str,
        content: str,
        source: str,
        prompt_template: str,
        model: Optional[str] = None,
        max_tokens: int = 800
    ) -> str:
        """
        生成文章摘要（带重试机制）
        
        Args:
            title: 文章标题
            content: 文章正文内容
            source: 文章来源
            prompt_template: 摘要生成 Prompt 模板
            model: 使用的模型，默认使用初始化时的模型
            max_tokens: 最大生成 token 数
            
        Returns:
            生成的摘要文本（Markdown 格式）
        """
        last_error = None
        use_model = model or self.model
        
        for attempt in range(self.max_retries):
            try:
                return await self._generate_summary_once(
                    title, content, source, prompt_template, use_model, max_tokens
                )
            except RateLimitError as e:
                last_error = e
                delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                print(f"    ⚠ API 限流，等待 {delay:.1f} 秒后重试 ({attempt + 1}/{self.max_retries})...")
                await asyncio.sleep(delay)
            except APIError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    print(f"    ⚠ API 错误，等待 {delay:.1f} 秒后重试 ({attempt + 1}/{self.max_retries})...")
                    await asyncio.sleep(delay)
                else:
                    raise
            except Exception as e:
                raise Exception(f"LLM API 调用失败: {str(e)}")
        
        raise Exception(f"LLM API 调用失败（已重试 {self.max_retries} 次）: {str(last_error)}")
    
    async def _generate_summary_once(
        self,
        title: str,
        content: str,
        source: str,
        prompt_template: str,
        model: str,
        max_tokens: int
    ) -> str:
        """
        单次摘要生成请求（内部方法）
        """
        # 构建文章内容（限制长度避免超出 token 限制）
        max_content_length = 8000
        truncated_content = content[:max_content_length] if len(content) > max_content_length else content
        
        article_content = f"""# {title}

- Source: {source}

## 正文内容

{truncated_content}
"""
        
        # 构建完整 Prompt
        full_prompt = f"{prompt_template}\n\n{article_content}\n\n## 请生成摘要"
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.5,
            max_tokens=max_tokens
        )
        
        summary = response.choices[0].message.content
        return summary.strip()
    
    async def batch_generate_summaries(
        self,
        articles: List[Dict[str, Any]],
        prompt_template: str,
        model: Optional[str] = None,
        max_concurrency: int = 5,
        summary_type: str = "deep"
    ) -> List[Dict[str, Any]]:
        """
        批量生成文章摘要
        
        Args:
            articles: 文章列表，每项包含 title, content, source, raw_summary
            prompt_template: 摘要生成 Prompt 模板
            model: 使用的模型，默认使用初始化时的模型
            max_concurrency: 最大并发数
            summary_type: 摘要类型标识（"deep" 或 "simple"）
            
        Returns:
            包含摘要结果的文章列表，每项新增 generated_summary, summary_type 字段
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def generate_with_semaphore(article: Dict[str, Any], index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    if (index + 1) % 5 == 0 or index == 0:
                        print(f"    进度: {index + 1}/{len(articles)}")
                    
                    # 获取正文内容，如果提取失败则使用标题和简介作为 fallback
                    content = article.get("content", "")
                    raw_summary = article.get("raw_summary", "")
                    
                    # 如果正文为空或太短，使用标题 + 简介作为 fallback
                    if not content or len(content) < 100:
                        if raw_summary:
                            content = f"【标题】{article.get('title', '')}\n\n【简介】{raw_summary}\n\n（注：正文提取失败，使用标题和简介生成摘要）"
                            print(f"    ⚠ 第 {index + 1} 条使用 fallback 内容（正文提取失败）")
                        else:
                            content = f"【标题】{article.get('title', '')}\n\n（注：正文提取失败，无简介可用）"
                            print(f"    ⚠ 第 {index + 1} 条内容不足（正文和简介均不可用）")
                    
                    result = await self.generate_summary_with_retry(
                        title=article.get("title", ""),
                        content=content,
                        source=article.get("source", ""),
                        prompt_template=prompt_template,
                        model=model
                    )
                    
                    return {
                        **article,
                        "generated_summary": result,
                        "summary_type": summary_type,
                        "summary_error": None
                    }
                except Exception as e:
                    return {
                        **article,
                        "generated_summary": None,
                        "summary_type": summary_type,
                        "summary_error": str(e)
                    }
        
        tasks = [generate_with_semaphore(article, i) for i, article in enumerate(articles)]
        results = await asyncio.gather(*tasks)
        
        return list(results)
    
    async def translate_title_with_retry(
        self,
        title: str,
        model: Optional[str] = None,
        max_tokens: int = 100
    ) -> str:
        """
        翻译标题为中文（带重试机制）
        
        Args:
            title: 英文标题
            model: 使用的模型，默认使用轻量级模型
            max_tokens: 最大生成 token 数
            
        Returns:
            翻译后的中文标题
        """
        last_error = None
        # 使用轻量级模型以提高速度
        use_model = model or "qwen-turbo"
        
        for attempt in range(self.max_retries):
            try:
                return await self._translate_title_once(title, use_model, max_tokens)
            except RateLimitError as e:
                last_error = e
                delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                print(f"    ⚠ API 限流，等待 {delay:.1f} 秒后重试 ({attempt + 1}/{self.max_retries})...")
                await asyncio.sleep(delay)
            except APIError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    print(f"    ⚠ API 错误，等待 {delay:.1f} 秒后重试 ({attempt + 1}/{self.max_retries})...")
                    await asyncio.sleep(delay)
                else:
                    raise
            except Exception as e:
                raise Exception(f"LLM API 调用失败: {str(e)}")
        
        raise Exception(f"LLM API 调用失败（已重试 {self.max_retries} 次）: {str(last_error)}")
    
    async def _translate_title_once(
        self,
        title: str,
        model: str,
        max_tokens: int
    ) -> str:
        """
        单次标题翻译请求（内部方法）
        """
        prompt = f"""请将以下英文科技新闻标题翻译为简洁、地道的中文标题。

        要求：
        1. 保持技术术语的准确性
        2. 翻译要简洁明了，不超过 30 个字
        3. 保留原标题中的关键信息
        4. 如果标题已经是中文，直接返回原标题
        5. 语序要符合中文习惯
        6. 具体公司名、产品名、人名的词汇不需要翻译

        原标题：{title}

        请只返回翻译后的中文标题，不要添加任何解释或额外内容。"""
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=max_tokens
        )
        
        translated_title = response.choices[0].message.content.strip()
        # 移除可能的引号
        translated_title = translated_title.strip('"\'')
        return translated_title
    
    async def batch_translate_titles(
        self,
        articles: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_concurrency: int = 5
    ) -> List[Dict[str, Any]]:
        """
        批量翻译文章标题
        
        Args:
            articles: 文章列表，每项包含 title
            model: 使用的模型，默认使用轻量级模型
            max_concurrency: 最大并发数
            
        Returns:
            包含翻译后标题的文章列表，每项新增 translated_title 字段
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def translate_with_semaphore(article: Dict[str, Any], index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    if (index + 1) % 5 == 0 or index == 0:
                        print(f"    翻译进度: {index + 1}/{len(articles)}")
                    
                    original_title = article.get("title", "")
                    
                    # 检查是否已经是中文（简单判断：如果包含中文字符则跳过翻译）
                    if any('\u4e00' <= char <= '\u9fff' for char in original_title):
                        translated = original_title
                        print(f"    第 {index + 1} 条标题已是中文，跳过翻译")
                    else:
                        translated = await self.translate_title_with_retry(
                            title=original_title,
                            model=model
                        )
                    
                    return {
                        **article,
                        "translated_title": translated,
                        "translation_error": None
                    }
                except Exception as e:
                    # 翻译失败时保留原标题
                    return {
                        **article,
                        "translated_title": article.get("title", ""),
                        "translation_error": str(e)
                    }
        
        tasks = [translate_with_semaphore(article, i) for i, article in enumerate(articles)]
        results = await asyncio.gather(*tasks)
        
        return list(results)


# 全局客户端实例
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    获取全局 LLM 客户端实例（单例模式）
    
    Returns:
        LLMClient 实例
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
