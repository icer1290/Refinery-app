"""
Agent 模块入口点
允许通过 `python -m src.agent` 运行
"""

import argparse
from src.agent import run_agent, run_single_node

if __name__ == "__main__":
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
