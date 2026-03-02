import feedparser
import time
import re
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.extraction import extract_content_from_url

# RSS 订阅清单
RSS_FEEDS = [
    # --- 核心科技媒体 (全领域覆盖) ---
    {"name": "Techmeme", "url": "https://www.techmeme.com/feed.xml"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
    {"name": "Wired (Science)", "url": "https://www.wired.com/feed/category/science/latest/rss"},
    
    # --- 顶级风投与趋势 (宏观视角/范式转移) ---
    {"name": "a16z", "url": "https://www.a16z.news/feed"},
    {"name": "Y Combinator", "url": "https://blog.ycombinator.com/feed/"},
    {"name": "Sequoia Capital", "url": "https://www.sequoiacap.com/feed/"},
    
    # --- AI 与巨头官报 (第一手重磅消息) ---
    {"name": "OpenAI Blog", "url": "https://openai.com/news/rss.xml"},
    {"name": "Google Blog", "url": "https://blog.google/rss/"},
    {"name": "Microsoft Blog", "url": "https://blogs.microsoft.com/feed/"},
    {"name": "Meta Newsroom", "url": "https://about.fb.com/news/feed/"},
    {"name": "NVIDIA Blog", "url": "https://blogs.nvidia.com/feed/"},
    
    # --- 硬核工程与架构 (技术创新度) ---
    {"name": "Netflix Tech Blog", "url": "https://netflixtechblog.com/feed"},
    {"name": "GitHub Engineering", "url": "https://github.blog/category/engineering/feed/"},
    {"name": "Cloudflare Blog", "url": "https://blog.cloudflare.com/rss/"},
    {"name": "InfoQ", "url": "https://www.infoq.com/feed"},
    {"name": "The New Stack", "url": "https://thenewstack.io/blog/feed/"},
    # {"name": "Dev.to", "url": "https://dev.to/feed"},
    
    # --- 深度专栏与分析 (主编视角洞察) ---
    {"name": "Stratechery (Ben Thompson)", "url": "https://stratechery.com/feed/"},
    {"name": "The Pragmatic Engineer", "url": "https://blog.pragmaticengineer.com/rss/"}
]

def clean_html(raw_html: str) -> str:
    """去除摘要中的 HTML 标签，保留纯文本"""
    if not raw_html: return ""
    clean_re = re.compile('<.*?>')
    clean_text = re.sub(clean_re, '', raw_html)
    # 处理一些常见的转义字符
    return clean_text.replace('&nbsp;', ' ').replace('&amp;', '&').strip()

def fetch_single_feed(feed_info: Dict[str, str], start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
    """单个 Feed 的抓取逻辑"""
    articles = []
    feed_name = feed_info["name"]
    feed_url = feed_info["url"]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml;q=0.9, image/webp, */*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        session = requests.Session()
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = session.get(feed_url, headers=headers, timeout=15, verify=False)

        if response.status_code == 403:
            print(f"Standard request failed for {feed_name}, trying fallback...")
            parsed_feed = feedparser.parse(feed_url)
        else:
            response.raise_for_status()
            parsed_feed = feedparser.parse(response.content)

        response.raise_for_status()
        
        parsed_feed = feedparser.parse(response.content)
        
        for entry in parsed_feed.entries:
            dt_tuple = entry.get('published_parsed') or entry.get('updated_parsed')
            if not dt_tuple:
                continue
            
            pub_date = datetime(*dt_tuple[:6], tzinfo=timezone.utc)
            
            if start_time <= pub_date <= end_time:
                article_url = entry.get("link", "")
                content = None
                
                if article_url:
                    content = extract_content_from_url(article_url, timeout=10)
                
                articles.append({
                    "title": entry.get("title", "No Title"),
                    "url": article_url,
                    "score": 0,
                    "source": feed_name,
                    "raw_summary": clean_html(entry.get("summary", "")),
                    "content": content,
                    "timestamp": int(pub_date.timestamp())
                })
    except Exception as e:
        print(f"Error fetching {feed_name}: {e}")
        
    return articles

def fetch_rss_feeds_parallel() -> List[Dict[str, Any]]:
    """
    并发获取所有 RSS 订阅源
    """
    now = datetime.now(timezone.utc)
    # 计算当前日期和 昨天的 8:00
    yesterday_8am = now.replace(hour=8, minute=0, second=0, microsecond=0) - timedelta(days=1)
    
    all_articles = []
    
    # 使用线程池加速: max_workers 根据 feed 数量调整
    with ThreadPoolExecutor(max_workers=len(RSS_FEEDS)) as executor:
        futures = [executor.submit(fetch_single_feed, f, yesterday_8am, now) for f in RSS_FEEDS]
        
        for future in as_completed(futures):
            all_articles.extend(future.result())
            
    # 按时间降序排序
    all_articles.sort(key=lambda x: x['timestamp'], reverse=True)
    return all_articles

if __name__ == "__main__":
    start_run = time.time()
    articles = fetch_rss_feeds_parallel()
    duration = time.time() - start_run
    
    print(f"抓取完成！用时: {duration:.2f}s")
    print(f"在时间窗口内找到 {len(articles)} 篇文章")
    
    # 打印简要统计
    for article in articles[:5]:
        print(f"- [{article['source']}] {article['title']} ({datetime.fromtimestamp(article['timestamp'])})")