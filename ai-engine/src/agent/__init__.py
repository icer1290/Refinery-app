"""
LangGraph Agent 主模块
实现科技新闻日报的完整工作流
"""

import sys
import os
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agent.state import GraphState, create_initial_state
from src.agent.nodes import (
    fetch_data_node,
    scoring_node,
    deep_extraction_node,
    summarize_node,
    delivery_node
)


def create_workflow(checkpoint_path: Optional[str] = None) -> StateGraph:
    """
    创建 LangGraph 工作流
    
    工作流节点：
    1. fetch_data - 从 Qdrant 提取当日新闻
    2. scoring - 批量打分与排序
    3. deep_extraction - 深度提取正文
    4. summarize - 分级摘要生成
    5. delivery - 邮件交付
    
    Args:
        checkpoint_path: SQLite 持久化路径，默认使用内存
        
    Returns:
        配置好的 StateGraph 实例
    """
    # 创建工作流
    workflow = StateGraph(GraphState)
    
    # 添加节点
    workflow.add_node("fetch_data", fetch_data_node)
    workflow.add_node("scoring", scoring_node)
    workflow.add_node("deep_extraction", deep_extraction_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("delivery", delivery_node)
    
    # 设置入口点
    workflow.set_entry_point("fetch_data")
    
    # 定义边（线性流程）
    workflow.add_edge("fetch_data", "scoring")
    workflow.add_edge("scoring", "deep_extraction")
    workflow.add_edge("deep_extraction", "summarize")
    workflow.add_edge("summarize", "delivery")
    workflow.add_edge("delivery", END)
    
    return workflow


def run_agent(
    thread_id: Optional[str] = None,
    checkpoint_path: str = "./checkpoints/checkpoints.sqlite"
) -> GraphState:
    """
    运行 Agent 工作流
    
    Args:
        thread_id: 线程 ID，用于断点续传，默认基于日期生成
        checkpoint_path: SQLite 持久化路径
        
    Returns:
        最终状态
    """
    print("=" * 60)
    print("科技新闻日报 Agent")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 生成 thread_id（基于日期，确保同一天运行使用相同的 ID）
    if thread_id is None:
        thread_id = datetime.now().strftime("%Y-%m-%d")
    print(f"Thread ID: {thread_id}")
    
    # 确保 checkpoint 目录存在
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    
    # 创建持久化器
    print(f"\n[初始化] 加载检查点: {checkpoint_path}")
    
    # 创建工作流
    workflow = create_workflow()
    
    # 编译工作流（带内存持久化）
    app = workflow.compile(
        checkpointer=MemorySaver()
    )
    
    # 创建初始状态
    initial_state = create_initial_state()
    
    # 配置
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # 运行工作流
    print("\n[启动] 开始执行工作流...\n")
    
    try:
        # 流式执行，可以看到每个节点的输出
        for event in app.stream(initial_state, config):
            # event 是字典，key 是节点名，value 是状态更新
            for node_name, state_update in event.items():
                if node_name != "__end__":
                    print(f"\n[完成] 节点: {node_name}")
        
        # 获取最终状态
        final_state = app.get_state(config).values
        
        print("\n" + "=" * 60)
        print("工作流执行完成")
        print("=" * 60)
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 输出统计
        print("\n执行统计:")
        print(f"  - 候选新闻数: {len(final_state.get('candidate_pool', []))}")
        print(f"  - Top 文章数: {len(final_state.get('top_articles', []))}")
        print(f"  - 摘要数: {len(final_state.get('summaries', []))}")
        print(f"  - 错误数: {len(final_state.get('error_logs', []))}")
        
        if final_state.get('error_logs'):
            print("\n错误日志:")
            for error in final_state['error_logs']:
                print(f"  - {error}")
        
        return final_state
        
    except Exception as e:
        print(f"\n✗ 工作流执行失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def run_single_node(node_name: str) -> GraphState:
    """
    单独运行某个节点（用于测试）
    
    Args:
        node_name: 节点名称 (fetch_data, scoring, deep_extraction, summarize, delivery)
        
    Returns:
        执行后的状态
    """
    from src.agent.nodes import NODE_FUNCTIONS
    
    if node_name not in NODE_FUNCTIONS:
        raise ValueError(f"未知节点: {node_name}，可用节点: {list(NODE_FUNCTIONS.keys())}")
    
    print("=" * 60)
    print(f"单独运行节点: {node_name}")
    print("=" * 60)
    
    # 创建初始状态
    state = create_initial_state()
    
    # 执行节点
    node_func = NODE_FUNCTIONS[node_name]
    result_state = node_func(state)
    
    print("\n" + "=" * 60)
    print("节点执行完成")
    print("=" * 60)
    
    return result_state


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="科技新闻日报 Agent")
    parser.add_argument(
        "--node",
        type=str,
        choices=["fetch_data", "scoring", "deep_extraction", "summarize", "delivery"],
        help="单独运行指定节点（用于测试）"
    )
    parser.add_argument(
        "--thread-id",
        type=str,
        help="线程 ID（用于断点续传）"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="./checkpoints/checkpoints.sqlite",
        help="检查点文件路径"
    )
    
    args = parser.parse_args()
    
    if args.node:
        # 单独运行某个节点
        run_single_node(args.node)
    else:
        # 运行完整工作流
        run_agent(
            thread_id=args.thread_id,
            checkpoint_path=args.checkpoint
        )
