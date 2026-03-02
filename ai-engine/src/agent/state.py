"""
LangGraph 全局状态定义
使用 TypedDict 确保各节点间数据的流转与断点续传
"""

from typing import List, Dict, TypedDict, Optional


class GraphState(TypedDict):
    """
    LangGraph 全局状态定义
    
    包含整个工作流中各节点需要共享的数据：
    - candidate_pool: 原始抓取的候选新闻池
    - top_articles: 当前选定的 Top 15 条目（含正文）
    - summaries: 已生成的摘要列表
    - error_logs: 错误日志，记录抓取失败的 URL
    - final_email: 最终 HTML 内容
    """
    
    # 原始抓取的候选新闻池
    # 格式: [{"title": str, "url": str, "source": str, "score": float, 
    #         "raw_summary": str, "timestamp": str, "inserted_at": str}, ...]
    candidate_pool: List[Dict]
    
    # 当前选定的 Top 15 条目（含正文）
    # 格式: [{"title": str, "url": str, "source": str, "score": float,
    #         "raw_summary": str, "content": str, "timestamp": str}, ...]
    top_articles: List[Dict]
    
    # 已生成的摘要列表
    # 格式: [{"title": str, "url": str, "summary": str, "level": str}, ...]
    # level: "deep" (Top 1-5) 或 "simple" (Top 6-15)
    summaries: List[Dict]
    
    # 错误日志，记录抓取失败的 URL
    # 格式: ["错误信息1", "错误信息2", ...]
    error_logs: List[str]
    
    # 最终 HTML 内容
    final_email: str


def create_initial_state() -> GraphState:
    """
    创建初始状态
    
    Returns:
        初始化的 GraphState 实例
    """
    return {
        "candidate_pool": [],
        "top_articles": [],
        "summaries": [],
        "error_logs": [],
        "final_email": ""
    }
