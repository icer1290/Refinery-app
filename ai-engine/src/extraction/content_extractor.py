"""
网页正文提取模块
使用 trafilatura 库从 URLs 中提取完整的正文内容
"""

import trafilatura
import requests
from typing import Optional, Dict, Any, List
import time
import asyncio
import aiohttp


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


def extract_content_from_url(url: str, timeout: int = 15) -> Optional[str]:
    """
    从 URL 提取正文内容
    
    Args:
        url: 目标网页 URL
        timeout: 请求超时时间（秒）
        
    Returns:
        提取的正文内容，如果提取失败返回 None
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        
        content = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
            include_images=False,
            include_links=False,
            output_format='txt',
            with_metadata=False
        )
        
        if content:
            return content.strip()
        
        return None
        
    except requests.RequestException as e:
        print(f"    请求失败 ({url}): {e}")
        return None
    except Exception as e:
        print(f"    提取失败 ({url}): {e}")
        return None


def extract_content_with_metadata(url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """
    从 URL 提取正文内容和元数据
    
    Args:
        url: 目标网页 URL
        timeout: 请求超时时间（秒）
        
    Returns:
        包含正文和元数据的字典，如果提取失败返回 None
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        
        # 提取正文和元数据
        result = trafilatura.extract_with_metadata(
            response.text,
            include_comments=False,
            include_tables=True,
            output_format='json',
            with_metadata=True,
            date_extraction=False
        )
        
        if result:
            return result
        
        return None
        
    except requests.RequestException as e:
        print(f"    请求失败 ({url}): {e}")
        return None
    except Exception as e:
        print(f"    提取失败 ({url}): {e}")
        return None


def extract_batch(urls: list, delay: float = 1.0, timeout: int = 15) -> Dict[str, Optional[str]]:
    """
    批量提取多个 URL 的正文内容
    
    Args:
        urls: URL 列表
        delay: 请求间隔时间（秒），避免过于频繁请求
        timeout: 请求超时时间（秒）
        
    Returns:
        URL 到正文内容的映射字典
    """
    results = {}
    
    for i, url in enumerate(urls):
        if i > 0 and delay > 0:
            time.sleep(delay)
        
        content = extract_content_from_url(url, timeout)
        results[url] = content
        
        if (i + 1) % 10 == 0:
            print(f"    进度: {i + 1}/{len(urls)}")
    
    return results


async def extract_article_content(url: str, timeout: int = 30) -> Optional[str]:
    """
    异步从 URL 提取正文内容
    
    Args:
        url: 目标网页 URL
        timeout: 请求超时时间（秒）
        
    Returns:
        提取的正文内容，如果提取失败返回 None
    """
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url, headers=HEADERS) as response:
                response.raise_for_status()
                html = await response.text()
                
                content = trafilatura.extract(
                    html,
                    include_comments=False,
                    include_tables=True,
                    include_images=False,
                    include_links=False,
                    output_format='txt',
                    with_metadata=False
                )
                
                if content:
                    return content.strip()
                
                return None
                
    except Exception as e:
        print(f"    异步提取失败 ({url}): {e}")
        return None


async def batch_extract_articles(articles: List[Dict[str, Any]], max_concurrency: int = 5, timeout: int = 30) -> List[Dict[str, Any]]:
    """
    异步批量提取文章正文内容
    
    Args:
        articles: 文章列表，每个文章字典必须包含 url 字段
        max_concurrency: 最大并发数
        timeout: 请求超时时间（秒）
        
    Returns:
        更新后的文章列表，每篇文章添加 content 和 content_length 字段
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def extract_single(article: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            url = article.get("url")
            if not url:
                article["content"] = None
                article["content_length"] = 0
                article["extraction_error"] = "No URL provided"
                return article
            
            try:
                content = await extract_article_content(url, timeout)
                if content:
                    article["content"] = content
                    article["content_length"] = len(content)
                    article["extraction_error"] = None
                else:
                    article["content"] = None
                    article["content_length"] = 0
                    article["extraction_error"] = "Content extraction returned empty"
            except Exception as e:
                article["content"] = None
                article["content_length"] = 0
                article["extraction_error"] = str(e)
            
            return article
    
    tasks = [extract_single(article.copy()) for article in articles]
    results = await asyncio.gather(*tasks)
    
    return results
