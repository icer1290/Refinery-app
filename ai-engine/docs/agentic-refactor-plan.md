# AI Engine Agentic 重构设计文档

## 1. 重构目标与背景

### 1.1 当前架构局限
- **线性管道**: 固定顺序执行，无动态决策
- **无记忆机制**: 无法积累用户偏好和历史反馈
- **有限工具**: 仅基础 API 调用，无扩展工具层
- **无质量保障**: 无自我校验和修正机制

### 1.2 目标架构
构建具备**四大核心设计模式**的 Agentic 系统：
- 反思 (Reflection)
- 工具使用 (Tool Use)
- 规划 (Planning)
- 多智能体协作 (Multi-agent)

同时实现完整的**记忆与状态管理**分层。

---

## 2. 四大核心设计模式实现

### 2.1 反思模式 (Reflection)

#### 2.1.1 架构设计
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   生成节点   │───▶│  质量检查节点 │───▶│  修正节点    │
└─────────────┘    └──────────────┘    └─────────────┘
                          │
                          ▼ (质量不达标)
                   ┌──────────────┐
                   │  返回重新生成  │
                   └──────────────┘
```

#### 2.1.2 关键实现

**新增文件**: `ai-engine/src/agent/nodes_reflection.py`

```python
# 质量检查节点 - 摘要质量评估
async def quality_check_summaries_node(state: GraphState) -> GraphState:
    """
    评估生成摘要的质量
    - 完整性检查：是否覆盖原文关键点
    - 准确性检查：是否与原文一致
    - 可读性检查：语言流畅度
    """
    quality_threshold = 0.7
    failed_items = []

    for summary in state["summaries"]:
        quality_score = await llm_client.evaluate_summary_quality(
            original=summary["content"],
            summary=summary["generated_summary"]
        )
        summary["quality_score"] = quality_score
        if quality_score < quality_threshold:
            failed_items.append(summary)

    state["needs_regeneration"] = len(failed_items) > 0
    state["regeneration_pool"] = failed_items
    return state

# 修正节点 - 重新生成低质量内容
async def regenerate_summaries_node(state: GraphState) -> GraphState:
    """对质量不达标的摘要进行重新生成"""
    if not state.get("needs_regeneration"):
        return state

    # 使用更详细的 prompt 和更高 temperature
    for item in state["regeneration_pool"]:
        improved_summary = await llm_client.generate_summary_with_retry(
            content=item["content"],
            prompt_template="detailed_summary_prompt.md",  # 使用更详细的模板
            temperature=0.5,  # 提高创造性
            feedback=item.get("quality_feedback", "")
        )
        item["generated_summary"] = improved_summary
        item["regeneration_count"] = item.get("regeneration_count", 0) + 1

    return state
```

**Prompt 模板**: `ai-engine/src/prompt/quality_check_prompt.md`

```markdown
# 质量评估 Prompt

你是一个严格的内容质量评估专家。请评估以下摘要的质量：

## 原文
{original_content}

## 摘要
{summary}

## 评估维度
1. **完整性** (0-1): 是否涵盖原文所有关键信息点
2. **准确性** (0-1): 信息是否与原文一致，无幻觉
3. **简洁性** (0-1): 是否简洁明了，无冗余
4. **可读性** (0-1): 语言是否流畅自然

## 输出格式
```json
{
  "overall_score": 0.85,
  "dimension_scores": {
    "completeness": 0.9,
    "accuracy": 0.8,
    "conciseness": 0.85,
    "readability": 0.9
  },
  "issues": ["问题1", "问题2"],
  "suggestions": "改进建议"
}
```
```

#### 2.1.3 条件路由配置
```python
# 在 workflow 中添加条件边
workflow.add_conditional_edges(
    "quality_check",
    lambda state: "regenerate" if state.get("needs_regeneration") else "continue",
    {
        "regenerate": "regenerate_summaries",
        "continue": "delivery"
    }
)

# 循环控制：最多重试 2 次
workflow.add_conditional_edges(
    "regenerate_summaries",
    lambda state: "quality_check" if all(
        item.get("regeneration_count", 0) < 2 for item in state["summaries"]
    ) else "delivery"
)
```

---

### 2.2 工具使用模式 (Tool Use)

#### 2.2.1 工具层架构
```
┌─────────────────────────────────────────────────────────────┐
│                      Tool Registry                          │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│  搜索工具    │  数据库工具  │  代码执行   │    内容处理       │
├─────────────┼─────────────┼─────────────┼───────────────────┤
│ web_search  │ query_pg    │ code_sandbox│ extract_pdf       │
│ news_search │ insert_pg   │ calc        │ extract_image     │
│ trend_search│ update_pg   │ validate    │ translate         │
└─────────────┴─────────────┴─────────────┴───────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     MCP Server Layer                        │
│  (标准化协议，支持外部工具接入)                                 │
└─────────────────────────────────────────────────────────────┘
```

#### 2.2.2 核心工具实现

**新增文件**: `ai-engine/src/tools/__init__.py`

```python
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import httpx

class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)

class Tool:
    """工具基类"""
    name: str
    description: str
    parameters: Dict

    async def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError

# ==================== 搜索工具 ====================

class WebSearchTool(Tool):
    """网络搜索工具 - 用于补充实时信息"""
    name = "web_search"
    description = "搜索网络获取最新信息"
    parameters = {
        "query": {"type": "string", "description": "搜索关键词"},
        "limit": {"type": "integer", "default": 5, "description": "返回结果数量"}
    }

    async def execute(self, query: str, limit: int = 5) -> ToolResult:
        try:
            # 使用 Serper API 或类似服务
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": settings.SERPER_API_KEY},
                    json={"q": query, "num": limit}
                )
                data = response.json()
                return ToolResult(
                    success=True,
                    data=data.get("organic", []),
                    metadata={"query": query, "result_count": len(data.get("organic", []))}
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

class TrendSearchTool(Tool):
    """科技趋势搜索 - 获取技术热点"""
    name = "trend_search"
    description = "获取特定技术领域的最新趋势"

    async def execute(self, topic: str) -> ToolResult:
        """搜索 GitHub Trending、Hacker News 等"""
        # 聚合多源数据
        pass

# ==================== 数据库工具 ====================

class PostgresQueryTool(Tool):
    """PostgreSQL 查询工具"""
    name = "query_postgres"
    description = "执行 PostgreSQL 查询"
    parameters = {
        "sql": {"type": "string", "description": "SQL 查询语句"},
        "params": {"type": "array", "description": "查询参数"}
    }

    async def execute(self, sql: str, params: List = None) -> ToolResult:
        import asyncpg
        try:
            conn = await asyncpg.connect(settings.POSTGRES_URL)
            rows = await conn.fetch(sql, *(params or []))
            await conn.close()
            return ToolResult(
                success=True,
                data=[dict(row) for row in rows],
                metadata={"row_count": len(rows)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

# ==================== 代码执行工具 ====================

class CodeExecutionTool(Tool):
    """安全代码执行沙盒"""
    name = "code_sandbox"
    description = "在沙盒环境中安全执行 Python 代码"
    parameters = {
        "code": {"type": "string", "description": "Python 代码"},
        "timeout": {"type": "integer", "default": 30, "description": "执行超时(秒)"}
    }

    async def execute(self, code: str, timeout: int = 30) -> ToolResult:
        # 使用 restrictedpython 或 Docker 沙盒
        import subprocess
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                ['python', temp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                # 限制资源使用
                # preexec_fn=limit_resources  # 需要额外实现
            )
            return ToolResult(
                success=result.returncode == 0,
                data=result.stdout,
                error=result.stderr if result.returncode != 0 else None
            )
        finally:
            os.unlink(temp_path)

# ==================== 内容处理工具 ====================

class ContentAnalysisTool(Tool):
    """内容分析工具 - 提取实体、关键词、情感"""
    name = "analyze_content"
    description = "分析内容提取关键信息"

    async def execute(self, content: str) -> ToolResult:
        # 调用 LLM 进行结构化分析
        analysis_prompt = f"""
        分析以下科技新闻内容，提取：
        1. 关键技术实体
        2. 核心创新点
        3. 情感倾向
        4. 技术成熟度评估

        内容：{content[:2000]}

        输出 JSON 格式。
        """
        result = await llm_client.generate_json(analysis_prompt)
        return ToolResult(success=True, data=result)
```

#### 2.2.3 MCP Server 实现

**新增文件**: `ai-engine/src/mcp/server.py`

```python
"""
MCP (Model Context Protocol) Server 实现
标准化工具接入协议
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio

app = FastAPI(title="TechNews MCP Server")

class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    context: Optional[Dict] = None

class ToolCallResponse(BaseModel):
    success: bool
    result: Any = None
    error: Optional[str] = None

# 工具注册表
tool_registry: Dict[str, Tool] = {}

def register_tool(tool: Tool):
    """注册工具到 MCP Server"""
    tool_registry[tool.name] = tool

@app.post("/mcp/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """MCP 标准工具调用接口"""
    tool = tool_registry.get(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {request.tool_name} not found")

    result = await tool.execute(**request.parameters)
    return ToolCallResponse(
        success=result.success,
        result=result.data,
        error=result.error
    )

@app.get("/mcp/tools")
async def list_tools():
    """列出所有可用工具"""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
        for tool in tool_registry.values()
    ]

# 初始化注册所有工具
@app.on_event("startup")
async def init_tools():
    register_tool(WebSearchTool())
    register_tool(PostgresQueryTool())
    register_tool(CodeExecutionTool())
    register_tool(ContentAnalysisTool())
```

#### 2.2.4 LLM 工具调用集成

**修改文件**: `ai-engine/src/llm/__init__.py`

```python
class ToolEnabledLLMClient(LLMClient):
    """支持工具调用的 LLM 客户端"""

    async def generate_with_tools(
        self,
        prompt: str,
        tools: List[Tool],
        max_tool_calls: int = 5
    ) -> Dict:
        """
        ReAct 风格工具调用
        - Thought: 思考需要做什么
        - Action: 调用工具
        - Observation: 观察结果
        - Final Answer: 最终回答
        """
        messages = [{"role": "user", "content": prompt}]
        tool_calls_made = 0

        while tool_calls_made < max_tool_calls:
            # 构建工具描述
            tools_desc = self._format_tools(tools)

            system_prompt = f"""
            你是一个可以使用工具的 AI 助手。

            可用工具：
            {tools_desc}

            请按以下格式回复：
            Thought: 你的思考过程
            Action: 工具名称(参数1=值1, 参数2=值2)
            或
            Final Answer: 最终回答
            """

            response = await self.chat_completion(
                messages=[{"role": "system", "content": system_prompt}] + messages
            )

            content = response.choices[0].message.content

            # 解析 Thought/Action/Final Answer
            if "Final Answer:" in content:
                return {
                    "final_answer": content.split("Final Answer:")[1].strip(),
                    "tool_calls": tool_calls_made
                }

            # 解析 Action
            action_match = re.search(r'Action:\s*(\w+)\((.*?)\)', content)
            if action_match:
                tool_name = action_match.group(1)
                params_str = action_match.group(2)
                params = self._parse_params(params_str)

                # 执行工具
                tool = next((t for t in tools if t.name == tool_name), None)
                if tool:
                    result = await tool.execute(**params)
                    tool_calls_made += 1

                    # 添加观察结果到上下文
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": f"Observation: {result.data if result.success else result.error}"
                    })

        return {"final_answer": content, "tool_calls": tool_calls_made}
```

---

### 2.3 规划模式 (Planning)

#### 2.3.1 动态规划架构
```
┌──────────────────────────────────────────────────────────────┐
│                       规划器 (Planner)                        │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   CoT 规划  │  │   ToT 规划   │  │   Re-planning       │  │
│  │  (简单任务)  │  │  (复杂决策)  │  │   (错误恢复)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                     执行计划 (Plan)                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │ 步骤1   │─▶│ 步骤2   │─▶│ 步骤3   │─▶│ 步骤4   │─▶│ 步骤5  │ │
│  └─────────┘  └────┬────┘  └─────────┘  └─────────┘  └────────┘ │
│                    │                                         │
│                    ▼ (条件分支)                                │
│              ┌─────────┐                                     │
│              │ 备选路径 │                                     │
│              └─────────┘                                     │
└──────────────────────────────────────────────────────────────┘
```

#### 2.3.2 规划器实现

**新增文件**: `ai-engine/src/agent/planner.py`

```python
"""
规划模块 - 支持 CoT、ToT 和动态重规划
"""
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

class PlanningStrategy(Enum):
    CHAIN_OF_THOUGHT = "cot"      # 线性链式思考
    TREE_OF_THOUGHTS = "tot"      # 树状多路径探索
    ADAPTIVE = "adaptive"         # 自适应选择

@dataclass
class PlanStep:
    """计划步骤"""
    id: str
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    condition: Optional[Callable] = None  # 执行条件
    max_retries: int = 2
    estimated_cost: float = 0.0  # 预估 Token 成本

@dataclass
class Plan:
    """执行计划"""
    steps: List[PlanStep]
    strategy: PlanningStrategy
    context: Dict = field(default_factory=dict)
    execution_log: List[Dict] = field(default_factory=list)

    def get_next_step(self, completed_steps: List[str], state: Dict) -> Optional[PlanStep]:
        """根据已完成步骤和当前状态获取下一步"""
        for step in self.steps:
            if step.id in completed_steps:
                continue
            # 检查依赖
            if all(dep in completed_steps for dep in step.dependencies):
                # 检查条件
                if step.condition is None or step.condition(state):
                    return step
        return None

class Planner:
    """规划器 - 生成和管理执行计划"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def create_plan(
        self,
        goal: str,
        context: Dict,
        strategy: PlanningStrategy = PlanningStrategy.ADAPTIVE
    ) -> Plan:
        """根据目标创建执行计划"""

        if strategy == PlanningStrategy.CHAIN_OF_THOUGHT:
            return await self._cot_planning(goal, context)
        elif strategy == PlanningStrategy.TREE_OF_THOUGHTS:
            return await self._tot_planning(goal, context)
        else:
            # 自适应选择
            complexity = await self._assess_complexity(goal, context)
            if complexity > 0.7:
                return await self._tot_planning(goal, context)
            return await self._cot_planning(goal, context)

    async def _cot_planning(self, goal: str, context: Dict) -> Plan:
        """CoT 线性规划"""
        prompt = f"""
        请将以下目标拆解为线性执行步骤：

        目标：{goal}
        上下文：{json.dumps(context, ensure_ascii=False)}

        要求：
        1. 步骤按执行顺序排列
        2. 每个步骤清晰可执行
        3. 考虑数据依赖关系

        输出 JSON 格式：
        {{
          "steps": [
            {{"id": "step1", "name": "步骤名称", "description": "详细描述", "dependencies": []}},
            {{"id": "step2", "name": "步骤名称", "description": "详细描述", "dependencies": ["step1"]}}
          ]
        }}
        """

        result = await self.llm.generate_json(prompt)
        steps = [PlanStep(**s) for s in result["steps"]]
        return Plan(steps=steps, strategy=PlanningStrategy.CHAIN_OF_THOUGHT)

    async def _tot_planning(self, goal: str, context: Dict) -> Plan:
        """
        ToT 树状规划
        - 生成多个候选路径
        - 评估每个路径的潜力
        - 选择最优路径
        """
        # 1. 生成候选路径
        candidates = await self._generate_candidate_plans(goal, context, n=3)

        # 2. 评估每个路径
        scored_candidates = []
        for candidate in candidates:
            score = await self._evaluate_plan(candidate, context)
            scored_candidates.append((candidate, score))

        # 3. 选择最佳路径
        best_plan = max(scored_candidates, key=lambda x: x[1])[0]
        best_plan.strategy = PlanningStrategy.TREE_OF_THOUGHTS

        return best_plan

    async def _generate_candidate_plans(self, goal: str, context: Dict, n: int) -> List[Plan]:
        """生成多个候选计划"""
        candidates = []
        for i in range(n):
            prompt = f"""
            为以下目标设计一个执行计划（方案 {i+1}/{n}）：
            目标：{goal}
            尝试采用不同的策略或侧重点。
            """
            result = await self.llm.generate_json(prompt)
            steps = [PlanStep(**s) for s in result["steps"]]
            candidates.append(Plan(steps=steps, strategy=PlanningStrategy.TREE_OF_THOUGHTS))
        return candidates

    async def _evaluate_plan(self, plan: Plan, context: Dict) -> float:
        """评估计划质量 (0-1)"""
        prompt = f"""
        评估以下计划的优劣：

        计划步骤：{[s.name for s in plan.steps]}
        上下文：{json.dumps(context, ensure_ascii=False)}

        评分维度：
        1. 完整性：是否覆盖所有必要步骤
        2. 效率：是否有冗余步骤
        3. 可行性：步骤是否可执行

        输出 0-1 之间的质量分数。
        """
        result = await self.llm.generate_json(prompt)
        return result.get("score", 0.5)

    async def replan(
        self,
        current_plan: Plan,
        failed_step: PlanStep,
        error: str,
        state: Dict
    ) -> Plan:
        """
        重新规划 - 当步骤失败时调整计划
        """
        prompt = f"""
        当前计划执行失败，需要重新规划：

        原计划步骤：{[s.name for s in current_plan.steps]}
        失败步骤：{failed_step.name}
        错误信息：{error}
        当前状态：{json.dumps(state, ensure_ascii=False)}

        请提供调整后的计划，可以：
        1. 添加前置步骤准备数据
        2. 修改失败步骤的实现方式
        3. 寻找替代路径

        输出新的步骤列表。
        """

        result = await self.llm.generate_json(prompt)
        new_steps = [PlanStep(**s) for s in result["steps"]]
        return Plan(
            steps=new_steps,
            strategy=PlanningStrategy.ADAPTIVE,
            context=current_plan.context
        )
```

#### 2.3.3 应用到新闻工作流

```python
# 在 nodes.py 中添加规划节点

async def planning_node(state: GraphState) -> GraphState:
    """
    根据当日数据特点动态规划处理流程
    """
    planner = Planner(llm_client)

    # 分析数据特征
    data_features = {
        "news_count": len(state.get("candidate_pool", [])),
        "sources": list(set(n.get("source") for n in state.get("candidate_pool", []))),
        "categories": list(set(n.get("category") for n in state.get("candidate_pool", []))),
        "avg_content_length": sum(len(n.get("content", "")) for n in state.get("candidate_pool", [])) / max(len(state.get("candidate_pool", [])), 1)
    }

    # 根据数据量选择策略
    if data_features["news_count"] > 100:
        strategy = PlanningStrategy.TREE_OF_THOUGHTS
        goal = "处理大量新闻，需要多级筛选和并行处理"
    else:
        strategy = PlanningStrategy.CHAIN_OF_THOUGHT
        goal = "处理常规数量新闻，标准流程"

    plan = await planner.create_plan(
        goal=goal,
        context=data_features,
        strategy=strategy
    )

    state["execution_plan"] = plan
    state["completed_steps"] = []
    return state
```

---

### 2.4 多智能体协作模式 (Multi-agent)

#### 2.4.1 架构设计
采用 **中心调度 (Hub-and-Spoke)** 模式：

```
                        ┌─────────────┐
                        │   协调器     │
                        │ (Orchestrator)│
                        └──────┬──────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   抓取 Agent   │    │   评分 Agent   │    │   摘要 Agent   │
│ (FetcherAgent)│    │ (ScoringAgent)│    │(SummaryAgent) │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        ▼                    ▼                    ▼
   抓取新闻数据           评分排序              生成摘要
   处理多源 RSS           质量评估              翻译标题
                        筛选 Top N            分级处理

        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  质检 Agent    │    │  交付 Agent    │    │  学习 Agent    │
│(QualityAgent) │    │(DeliveryAgent)│    │ (LearningAgent)│
└───────────────┘    └───────────────┘    └───────────────┘
   内容质量检查          邮件生成发送           反馈学习
   自我反思修正          用户偏好适配           持续优化
```

#### 2.4.2 Agent 基类与实现

**新增文件**: `ai-engine/src/agent/agents/base.py`

```python
"""
Agent 基类 - 支持多 Agent 协作
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio

class AgentRole(Enum):
    FETCHER = "fetcher"           # 数据抓取
    SCORING = "scoring"           # 评分排序
    EXTRACTION = "extraction"     # 内容提取
    SUMMARY = "summary"           # 摘要生成
    QUALITY = "quality"           # 质量检查
    DELIVERY = "delivery"         # 交付发送
    LEARNING = "learning"         # 学习优化
    ORCHESTRATOR = "orchestrator" # 协调器

@dataclass
class AgentMessage:
    """Agent 间消息"""
    sender: str
    receiver: str
    message_type: str  # task, result, feedback, query
    content: Any
    metadata: Dict = None

class Agent(ABC):
    """Agent 基类"""

    def __init__(self, role: AgentRole, llm_client, tools: List = None):
        self.role = role
        self.llm = llm_client
        self.tools = tools or []
        self.memory = []  # 短期记忆
        self.message_queue = asyncio.Queue()

    @abstractmethod
    async def process(self, task: Dict) -> Dict:
        """处理任务"""
        pass

    async def send_message(self, receiver: str, content: Any, msg_type: str = "task"):
        """向其他 Agent 发送消息"""
        msg = AgentMessage(
            sender=self.role.value,
            receiver=receiver,
            message_type=msg_type,
            content=content
        )
        # 通过消息总线发送
        await message_bus.send(msg)

    async def receive_message(self) -> AgentMessage:
        """接收消息"""
        return await self.message_queue.get()

    def add_to_memory(self, item: Dict):
        """添加到短期记忆"""
        self.memory.append(item)
        # 限制记忆长度
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]

    async def use_tool(self, tool_name: str, **params) -> Any:
        """使用工具"""
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if tool:
            result = await tool.execute(**params)
            return result
        raise ValueError(f"Tool {tool_name} not found")
```

**新增文件**: `ai-engine/src/agent/agents/fetcher_agent.py`

```python
"""
抓取 Agent - 负责多源数据采集
"""
from .base import Agent, AgentRole

class FetcherAgent(Agent):
    """新闻抓取 Agent"""

    def __init__(self, llm_client, vector_store):
        super().__init__(AgentRole.FETCHER, llm_client)
        self.vector_store = vector_store

    async def process(self, task: Dict) -> Dict:
        """
        执行抓取任务
        支持多源并行抓取
        """
        sources = task.get("sources", ["rss", "hackernews", "github"])
        results = []

        # 并行抓取多个源
        tasks = []
        for source in sources:
            if source == "rss":
                tasks.append(self._fetch_rss())
            elif source == "hackernews":
                tasks.append(self._fetch_hackernews())
            elif source == "github":
                tasks.append(self._fetch_github_trending())

        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        for source, result in zip(sources, all_results):
            if isinstance(result, Exception):
                results.append({"source": source, "status": "error", "error": str(result)})
            else:
                results.append({"source": source, "status": "success", "count": len(result)})
                # 去重后存储
                await self._store_unique(result)

        return {
            "status": "completed",
            "sources_processed": len(sources),
            "results": results
        }

    async def _fetch_rss(self) -> List[Dict]:
        """抓取 RSS 源"""
        from ingestion.rss_feeds import fetch_all_feeds
        return await fetch_all_feeds()

    async def _fetch_hackernews(self) -> List[Dict]:
        """抓取 Hacker News"""
        # 实现 HN 抓取
        pass

    async def _fetch_github_trending(self) -> List[Dict]:
        """抓取 GitHub Trending"""
        # 使用工具调用
        result = await self.use_tool("github_trending", language="python")
        return result.data if result.success else []

    async def _store_unique(self, articles: List[Dict]):
        """语义去重后存储"""
        from preprocessing.semantic_dedup import SemanticDeduplicator
        dedup = SemanticDeduplicator()
        unique = await dedup.deduplicate(articles)
        await self.vector_store.upsert_news(unique)
```

**新增文件**: `ai-engine/src/agent/agents/scoring_agent.py`

```python
"""
评分 Agent - 负责新闻质量评估和排序
"""
from .base import Agent, AgentRole
import asyncio

class ScoringAgent(Agent):
    """新闻评分 Agent"""

    def __init__(self, llm_client):
        super().__init__(AgentRole.SCORING, llm_client)

    async def process(self, task: Dict) -> Dict:
        """
        对新闻进行多维度评分
        """
        articles = task.get("articles", [])
        scoring_criteria = task.get("criteria", {
            "technical_depth": 0.3,
            "innovation": 0.3,
            "practical_value": 0.2,
            "timeliness": 0.2
        })

        # 批量评分
        scored_articles = await self._batch_score(articles, scoring_criteria)

        # 排序
        scored_articles.sort(key=lambda x: x["final_score"], reverse=True)

        # 返回 Top N
        top_n = task.get("top_n", 25)
        return {
            "status": "completed",
            "total_scored": len(scored_articles),
            "top_articles": scored_articles[:top_n],
            "candidate_pool": scored_articles[top_n:top_n*2]
        }

    async def _batch_score(self, articles: List[Dict], criteria: Dict) -> List[Dict]:
        """批量评分"""
        semaphore = asyncio.Semaphore(5)

        async def score_one(article):
            async with semaphore:
                # 构建评分提示
                prompt = f"""
                对以下科技新闻进行多维度评分：

                标题：{article.get('title')}
                内容：{article.get('content', '')[:1000]}
                来源：{article.get('source')}

                评分维度 (0-10)：
                1. technical_depth: 技术深度
                2. innovation: 创新性
                3. practical_value: 实用价值
                4. timeliness: 时效性

                输出 JSON 格式。
                """

                result = await self.llm.generate_json(prompt)

                # 计算加权总分
                final_score = sum(
                    result.get(k, 5) * w for k, w in criteria.items()
                )

                article["llm_scores"] = result
                article["final_score"] = final_score
                return article

        tasks = [score_one(a) for a in articles]
        return await asyncio.gather(*tasks)
```

**新增文件**: `ai-engine/src/agent/agents/quality_agent.py`

```python
"""
质检 Agent - 负责质量检查和反思修正
"""
from .base import Agent, AgentRole

class QualityAgent(Agent):
    """质量检查 Agent - 实现 Reflection 模式"""

    def __init__(self, llm_client):
        super().__init__(AgentRole.QUALITY, llm_client)

    async def process(self, task: Dict) -> Dict:
        """
        执行质量检查
        """
        content_type = task.get("type")  # "summary", "extraction", "translation"
        content = task.get("content")

        if content_type == "summary":
            return await self._check_summary_quality(task)
        elif content_type == "extraction":
            return await self._check_extraction_quality(task)
        elif content_type == "translation":
            return await self._check_translation_quality(task)

        return {"status": "unknown_type"}

    async def _check_summary_quality(self, task: Dict) -> Dict:
        """检查摘要质量"""
        original = task.get("original_content")
        summary = task.get("summary")

        # 多维度评估
        checks = await asyncio.gather(
            self._check_completeness(original, summary),
            self._check_accuracy(original, summary),
            self._check_readability(summary)
        )

        overall_score = sum(c["score"] for c in checks) / len(checks)

        return {
            "status": "passed" if overall_score > 0.7 else "failed",
            "overall_score": overall_score,
            "checks": checks,
            "feedback": self._generate_feedback(checks)
        }

    async def _check_completeness(self, original: str, summary: str) -> Dict:
        """检查完整性"""
        prompt = f"""
        评估摘要是否完整覆盖原文关键点：

        原文：{original[:1500]}
        摘要：{summary}

        请列出原文的关键点，并检查摘要是否覆盖。
        返回：{{"score": 0-1, "missed_points": ["..."]}}
        """
        return await self.llm.generate_json(prompt)

    async def _check_accuracy(self, original: str, summary: str) -> Dict:
        """检查准确性 - 是否有幻觉"""
        prompt = f"""
        检查摘要中是否存在与原文不符的信息：

        原文：{original[:1500]}
        摘要：{summary}

        逐句比对，标记任何不准确或无法验证的信息。
        返回：{{"score": 0-1, "hallucinations": ["..."]}}
        """
        return await self.llm.generate_json(prompt)

    async def _check_readability(self, summary: str) -> Dict:
        """检查可读性"""
        # 规则 + LLM 混合检查
        score = 1.0
        issues = []

        # 规则检查
        if len(summary) < 50:
            score -= 0.3
            issues.append("摘要过短")
        if len(summary) > 500:
            score -= 0.2
            issues.append("摘要偏长")

        # LLM 语言质量检查
        prompt = f"""
        评估以下摘要的语言质量：
        {summary}

        检查：流畅度、专业性、语法错误
        返回：{{"score": 0-1, "suggestions": "..."}}
        """
        llm_result = await self.llm.generate_json(prompt)

        return {
            "score": (score + llm_result.get("score", 1)) / 2,
            "issues": issues,
            "suggestions": llm_result.get("suggestions", "")
        }

    def _generate_feedback(self, checks: List[Dict]) -> str:
        """生成改进建议"""
        feedback_parts = []
        for check in checks:
            if check["score"] < 0.7:
                feedback_parts.append(f"{check.get('dimension', '质量')}: {check.get('suggestions', '需要改进')}")
        return "; ".join(feedback_parts) if feedback_parts else "质量良好"
```

#### 2.4.3 协调器实现

**新增文件**: `ai-engine/src/agent/agents/orchestrator.py`

```python
"""
协调器 - 中心调度模式的核心
"""
from .base import Agent, AgentRole, AgentMessage
from typing import Dict, List
import asyncio

class OrchestratorAgent(Agent):
    """
    协调器 Agent
    - 接收用户请求
    - 分解任务并分配给各个 Agent
    - 监控执行进度
    - 处理 Agent 间协作
    """

    def __init__(self, llm_client):
        super().__init__(AgentRole.ORCHESTRATOR, llm_client)
        self.agents: Dict[str, Agent] = {}
        self.task_status: Dict[str, Dict] = {}

    def register_agent(self, agent: Agent):
        """注册 Agent"""
        self.agents[agent.role.value] = agent

    async def process(self, task: Dict) -> Dict:
        """
        协调多 Agent 完成任务
        """
        task_type = task.get("type", "daily_newsletter")

        if task_type == "daily_newsletter":
            return await self._coordinate_daily_newsletter(task)
        elif task_type == "custom_query":
            return await self._coordinate_custom_query(task)
        else:
            return {"status": "error", "message": f"Unknown task type: {task_type}"}

    async def _coordinate_daily_newsletter(self, task: Dict) -> Dict:
        """协调每日新闻简报生成"""
        results = {}

        # Step 1: 抓取 Agent
        print("[Orchestrator] Phase 1: Data Fetching")
        fetch_result = await self.agents["fetcher"].process({
            "sources": task.get("sources", ["rss", "hackernews"])
        })
        results["fetch"] = fetch_result

        # Step 2: 评分 Agent
        print("[Orchestrator] Phase 2: Scoring")
        # 从 Qdrant 获取今日新闻
        articles = await self._fetch_today_articles()
        score_result = await self.agents["scoring"].process({
            "articles": articles,
            "top_n": 25
        })
        results["scoring"] = score_result

        # Step 3: 提取 Agent (并行处理 Top 25)
        print("[Orchestrator] Phase 3: Content Extraction")
        top_articles = score_result["top_articles"]
        extraction_result = await self._parallel_extraction(top_articles)
        results["extraction"] = extraction_result

        # Step 4: 摘要 Agent (分级处理)
        print("[Orchestrator] Phase 4: Summarization")
        extracted = extraction_result["extracted"]
        summary_result = await self.agents["summary"].process({
            "articles": extracted,
            "deep_summary_count": 15  # Top 15 深度摘要
        })
        results["summary"] = summary_result

        # Step 5: 质检 Agent (Reflection)
        print("[Orchestrator] Phase 5: Quality Check")
        summaries = summary_result["summaries"]
        quality_result = await self._batch_quality_check(summaries)
        results["quality"] = quality_result

        # 重生成低质量内容
        if quality_result["needs_regeneration"]:
            print("[Orchestrator] Regenerating low-quality summaries...")
            await self._regenerate_low_quality(quality_result["failed_items"])

        # Step 6: 交付 Agent
        print("[Orchestrator] Phase 6: Delivery")
        delivery_result = await self.agents["delivery"].process({
            "summaries": summaries,
            "template": task.get("template", "default")
        })
        results["delivery"] = delivery_result

        return {
            "status": "completed",
            "phases": results
        }

    async def _batch_quality_check(self, summaries: List[Dict]) -> Dict:
        """批量质量检查"""
        semaphore = asyncio.Semaphore(3)

        async def check_one(summary):
            async with semaphore:
                return await self.agents["quality"].process({
                    "type": "summary",
                    "original_content": summary.get("content"),
                    "summary": summary.get("generated_summary")
                })

        checks = await asyncio.gather(*[check_one(s) for s in summaries])

        failed = [s for s, c in zip(summaries, checks) if c["status"] == "failed"]

        return {
            "overall_pass_rate": sum(1 for c in checks if c["status"] == "passed") / len(checks),
            "needs_regeneration": len(failed) > 0,
            "failed_items": failed
        }

    async def _regenerate_low_quality(self, failed_items: List[Dict]):
        """重新生成低质量内容"""
        for item in failed_items:
            # 使用更高质量的配置重新生成
            new_summary = await self.agents["summary"].process({
                "articles": [item],
                "model": "qwen3-30b-a3b-instruct-2507",  # 确保使用最强模型
                "temperature": 0.3,  # 降低随机性
                "prompt_template": "detailed_summary_prompt.md"
            })
            item["generated_summary"] = new_summary["summaries"][0]["generated_summary"]
            item["regenerated"] = True

    async def handle_agent_message(self, message: AgentMessage):
        """处理 Agent 间消息"""
        # 根据消息类型路由
        if message.message_type == "result":
            # 更新任务状态
            pass
        elif message.message_type == "query":
            # 转发给其他 Agent
            target_agent = self.agents.get(message.receiver)
            if target_agent:
                await target_agent.message_queue.put(message)
        elif message.message_type == "feedback":
            # 学习 Agent 接收反馈
            learning_agent = self.agents.get("learning")
            if learning_agent:
                await learning_agent.process({
                    "type": "feedback",
                    "content": message.content
                })
```

---

## 3. 记忆与状态管理

### 3.1 记忆分层架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         记忆管理层                                   │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│   短期记忆    │   工作记忆    │   长期记忆    │      情景记忆          │
├──────────────┼──────────────┼──────────────┼───────────────────────┤
│ 当前会话上下文 │ 中间计算结果  │  用户偏好     │    历史会话记录        │
│ 对话历史     │ 临时变量      │  领域知识     │    已解决问题          │
│ 最近输入输出 │ 缓存数据      │  反馈历史     │    成功案例            │
├──────────────┼──────────────┼──────────────┼───────────────────────┤
│  Context     │   State      │   RAG Store  │    Memory Store       │
│  Window      │  (GraphState)│  (Qdrant)    │    (PostgreSQL)       │
└──────────────┴──────────────┴─────────────┘───────────────────────┘
```

### 3.2 增强状态定义

**修改文件**: `ai-engine/src/agent/state.py`

```python
from typing import List, Dict, TypedDict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

class GraphState(TypedDict):
    # ==================== 原始字段 ====================
    candidate_pool: List[Dict]
    top_articles: List[Dict]
    summaries: List[Dict]
    error_logs: List[str]
    final_email: str

    # ==================== 短期记忆 ====================
    conversation_history: List[Dict]  # 对话历史
    recent_actions: List[Dict]        # 最近执行的动作
    context_window: Dict              # 当前上下文窗口

    # ==================== 工作记忆 ====================
    execution_plan: Optional[Any]     # 执行计划
    completed_steps: List[str]        # 已完成步骤
    intermediate_results: Dict        # 中间结果缓存
    temp_variables: Dict              # 临时变量

    # ==================== 质量与反思 ====================
    quality_scores: List[Dict]        # 质量评分记录
    needs_regeneration: bool          # 是否需要重生成
    regeneration_pool: List[Dict]     # 待重生成内容
    reflection_notes: List[str]       # 反思笔记

    # ==================== 元数据 ====================
    execution_metadata: Dict          # 执行元数据
        # - start_time
        # - step_timings
        # - token_usage
        # - api_calls
    user_preferences: Dict            # 用户偏好
        # - preferred_categories
        # - preferred_sources
        # - summary_length_pref
    system_status: Dict               # 系统状态
        # - current_phase
        # - last_checkpoint
        # - recovery_point

# ==================== 长期记忆模型 ====================

@dataclass
class UserPreference:
    """用户偏好 - 持久化存储"""
    user_id: str
    preferred_categories: List[str] = field(default_factory=list)
    preferred_sources: List[str] = field(default_factory=list)
    summary_depth: str = "medium"  # brief, medium, detailed
    interest_keywords: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class FeedbackRecord:
    """用户反馈记录"""
    id: str
    user_id: str
    content_id: str
    feedback_type: str  # like, dislike, correction
    feedback_content: str
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class LearningPattern:
    """学习到的模式"""
    pattern_type: str  # scoring_pattern, summary_pattern, etc.
    pattern_data: Dict
    confidence: float
    sample_count: int
    last_updated: datetime = field(default_factory=datetime.utcnow)
```

### 3.3 记忆管理器实现

**新增文件**: `ai-engine/src/memory/__init__.py`

```python
"""
记忆管理模块 - 分层记忆管理
"""
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
import json
from datetime import datetime, timedelta
import redis.asyncio as redis
import asyncpg

class MemoryLayer(ABC):
    """记忆层基类"""

    @abstractmethod
    async def store(self, key: str, value: Any, ttl: Optional[int] = None):
        pass

    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def delete(self, key: str):
        pass

class ShortTermMemory(MemoryLayer):
    """
    短期记忆 - Redis 存储
    - 当前会话上下文
    - 最近交互历史
    - 临时缓存
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    async def store(self, key: str, value: Any, ttl: Optional[int] = 3600):
        """存储短期记忆，默认1小时过期"""
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value, default=str)
        )

    async def retrieve(self, key: str) -> Optional[Any]:
        """检索短期记忆"""
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def append_to_conversation(self, session_id: str, message: Dict):
        """追加到对话历史"""
        key = f"conversation:{session_id}"
        # 获取现有历史
        history = await self.retrieve(key) or []
        history.append({
            **message,
            "timestamp": datetime.utcnow().isoformat()
        })
        # 限制历史长度 (最近 20 条)
        history = history[-20:]
        await self.store(key, history, ttl=86400)  # 24小时

    async def get_conversation_context(self, session_id: str) -> List[Dict]:
        """获取对话上下文"""
        return await self.retrieve(f"conversation:{session_id}") or []

    async def delete(self, key: str):
        await self.redis.delete(key)

class WorkingMemory:
    """
    工作记忆 - 内存中状态
    - 当前 GraphState
    - 中间计算结果
    - 临时变量
    """

    def __init__(self):
        self._state: Dict = {}
        self._cache: Dict = {}
        self._timestamps: Dict = {}

    def get(self, key: str) -> Any:
        """获取工作记忆"""
        return self._state.get(key)

    def set(self, key: str, value: Any):
        """设置工作记忆"""
        self._state[key] = value
        self._timestamps[key] = datetime.utcnow()

    def cache_computation(self, key: str, value: Any, ttl_seconds: int = 300):
        """缓存计算结果"""
        self._cache[key] = {
            "value": value,
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl_seconds)
        }

    def get_cached(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            cache_entry = self._cache[key]
            if cache_entry["expires_at"] > datetime.utcnow():
                return cache_entry["value"]
            else:
                del self._cache[key]
        return None

    def clear(self):
        """清空工作记忆"""
        self._state.clear()
        self._cache.clear()

class LongTermMemory(MemoryLayer):
    """
    长期记忆 - PostgreSQL + Qdrant
    - 用户偏好
    - 历史反馈
    - 领域知识 (RAG)
    """

    def __init__(self, pg_url: str, qdrant_client):
        self.pg_url = pg_url
        self.qdrant = qdrant_client

    async def init_tables(self):
        """初始化数据库表"""
        conn = await asyncpg.connect(self.pg_url)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id VARCHAR(255) PRIMARY KEY,
                preferred_categories JSONB DEFAULT '[]',
                preferred_sources JSONB DEFAULT '[]',
                summary_depth VARCHAR(20) DEFAULT 'medium',
                interest_keywords JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS feedback_records (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255),
                content_id VARCHAR(255),
                feedback_type VARCHAR(50),
                feedback_content TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS learning_patterns (
                pattern_type VARCHAR(100) PRIMARY KEY,
                pattern_data JSONB,
                confidence FLOAT DEFAULT 0.0,
                sample_count INT DEFAULT 0,
                last_updated TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS session_memory (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255),
                summary TEXT,
                key_points JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.close()

    async def store_user_preference(self, user_id: str, preferences: Dict):
        """存储用户偏好"""
        conn = await asyncpg.connect(self.pg_url)
        await conn.execute("""
            INSERT INTO user_preferences (user_id, preferred_categories, preferred_sources, summary_depth, interest_keywords)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id) DO UPDATE SET
                preferred_categories = $2,
                preferred_sources = $3,
                summary_depth = $4,
                interest_keywords = $5,
                updated_at = NOW()
        """, user_id,
            json.dumps(preferences.get("categories", [])),
            json.dumps(preferences.get("sources", [])),
            preferences.get("summary_depth", "medium"),
            json.dumps(preferences.get("keywords", []))
        )
        await conn.close()

    async def get_user_preference(self, user_id: str) -> Optional[Dict]:
        """获取用户偏好"""
        conn = await asyncpg.connect(self.pg_url)
        row = await conn.fetchrow(
            "SELECT * FROM user_preferences WHERE user_id = $1",
            user_id
        )
        await conn.close()
        return dict(row) if row else None

    async def store_feedback(self, user_id: str, content_id: str, feedback_type: str, content: str):
        """存储用户反馈"""
        conn = await asyncpg.connect(self.pg_url)
        await conn.execute("""
            INSERT INTO feedback_records (user_id, content_id, feedback_type, feedback_content)
            VALUES ($1, $2, $3, $4)
        """, user_id, content_id, feedback_type, content)
        await conn.close()

    async def get_similar_feedback(self, content_id: str, limit: int = 10) -> List[Dict]:
        """获取相似内容的反馈 (RAG 检索)"""
        # 使用 Qdrant 检索相似内容
        similar = await self.qdrant.search_similar(content_id, limit)
        content_ids = [s.id for s in similar]

        conn = await asyncpg.connect(self.pg_url)
        rows = await conn.fetch("""
            SELECT * FROM feedback_records
            WHERE content_id = ANY($1)
            ORDER BY created_at DESC
        """, content_ids)
        await conn.close()
        return [dict(r) for r in rows]

    async def store_knowledge(self, content: str, metadata: Dict):
        """存储领域知识到 RAG"""
        # 生成 embedding 并存储到 Qdrant
        from embeddings import EmbeddingClient
        embed_client = EmbeddingClient()
        embedding = await embed_client.embed(content)

        await self.qdrant.upsert(
            vectors=[embedding],
            payloads=[{"content": content, **metadata}]
        )

    async def query_knowledge(self, query: str, limit: int = 5) -> List[Dict]:
        """RAG 检索知识"""
        from embeddings import EmbeddingClient
        embed_client = EmbeddingClient()
        query_embedding = await embed_client.embed(query)

        results = await self.qdrant.search(
            vector=query_embedding,
            limit=limit
        )
        return [r.payload for r in results]

    async def store(self, key: str, value: Any, ttl: Optional[int] = None):
        """长期记忆存储"""
        conn = await asyncpg.connect(self.pg_url)
        await conn.execute("""
            INSERT INTO session_memory (session_id, summary, key_points)
            VALUES ($1, $2, $3)
            ON CONFLICT (session_id) DO UPDATE SET
                summary = $2,
                key_points = $3
        """, key, json.dumps(value), json.dumps({}))
        await conn.close()

    async def retrieve(self, key: str) -> Optional[Any]:
        """长期记忆检索"""
        conn = await asyncpg.connect(self.pg_url)
        row = await conn.fetchrow(
            "SELECT * FROM session_memory WHERE session_id = $1",
            key
        )
        await conn.close()
        return json.loads(row["summary"]) if row else None

    async def delete(self, key: str):
        conn = await asyncpg.connect(self.pg_url)
        await conn.execute(
            "DELETE FROM session_memory WHERE session_id = $1",
            key
        )
        await conn.close()

class EpisodicMemory:
    """
    情景记忆 - 记录历史会话和成功案例
    用于 few-shot learning 和案例检索
    """

    def __init__(self, pg_url: str):
        self.pg_url = pg_url

    async def record_episode(self, episode: Dict):
        """记录一个完整 episode"""
        conn = await asyncpg.connect(self.pg_url)
        await conn.execute("""
            INSERT INTO episodes (episode_type, input_data, output_data, success, learnings)
            VALUES ($1, $2, $3, $4, $5)
        """,
            episode.get("type"),
            json.dumps(episode.get("input")),
            json.dumps(episode.get("output")),
            episode.get("success", True),
            json.dumps(episode.get("learnings", []))
        )
        await conn.close()

    async def retrieve_similar_episodes(self, query: Dict, limit: int = 3) -> List[Dict]:
        """检索相似历史案例"""
        # 基于关键词匹配
        conn = await asyncpg.connect(self.pg_url)
        # 简化实现：按类型和成功状态过滤
        rows = await conn.fetch("""
            SELECT * FROM episodes
            WHERE episode_type = $1 AND success = true
            ORDER BY created_at DESC
            LIMIT $2
        """, query.get("type"), limit)
        await conn.close()
        return [dict(r) for r in rows]

class MemoryManager:
    """
    记忆管理器 - 统一接口管理所有记忆层
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        pg_url: str = "postgresql://localhost/technews",
        qdrant_client = None
    ):
        self.short_term = ShortTermMemory(redis_url)
        self.working = WorkingMemory()
        self.long_term = LongTermMemory(pg_url, qdrant_client)
        self.episodic = EpisodicMemory(pg_url)

    async def init(self):
        """初始化记忆系统"""
        await self.long_term.init_tables()

    async def remember(
        self,
        key: str,
        value: Any,
        memory_type: str = "short_term",
        ttl: Optional[int] = None
    ):
        """
        存储记忆
        memory_type: short_term, working, long_term, episodic
        """
        if memory_type == "short_term":
            await self.short_term.store(key, value, ttl)
        elif memory_type == "working":
            self.working.set(key, value)
        elif memory_type == "long_term":
            await self.long_term.store(key, value)
        elif memory_type == "episodic":
            await self.episodic.record_episode(value)

    async def recall(
        self,
        key: str,
        memory_type: str = "short_term"
    ) -> Optional[Any]:
        """检索记忆"""
        if memory_type == "short_term":
            return await self.short_term.retrieve(key)
        elif memory_type == "working":
            return self.working.get(key)
        elif memory_type == "long_term":
            return await self.long_term.retrieve(key)
        return None

    async def get_context_for_llm(self, session_id: str, user_id: Optional[str] = None) -> Dict:
        """
        为 LLM 调用组装上下文
        包含：短期记忆 + 用户偏好 + 相关历史
        """
        context = {
            "conversation_history": [],
            "user_preferences": {},
            "relevant_knowledge": []
        }

        # 短期记忆
        context["conversation_history"] = await self.short_term.get_conversation_context(session_id)

        # 用户偏好
        if user_id:
            context["user_preferences"] = await self.long_term.get_user_preference(user_id) or {}

        # 相关领域知识 (RAG)
        if context["conversation_history"]:
            last_message = context["conversation_history"][-1].get("content", "")
            context["relevant_knowledge"] = await self.long_term.query_knowledge(last_message, limit=3)

        return context
```

---

## 4. 渐进式重构路线图

### 阶段 1: 基础改造 (2周)

#### Week 1: 状态管理升级
1. **修改 `state.py`** - 添加增强状态字段
2. **实现 `memory/__init__.py`** - 基础记忆管理器
3. **集成到现有节点** - 节点读写增强状态

#### Week 2: 反思模式
1. **创建 `nodes_reflection.py`** - 质量检查和修正节点
2. **添加质量评估 Prompt** - `quality_check_prompt.md`
3. **修改 workflow** - 添加条件边支持循环

### 阶段 2: 工具层建设 (2周)

#### Week 3: 工具框架
1. **创建 `tools/__init__.py`** - 工具基类和实现
2. **实现核心工具** - 搜索、数据库、代码执行
3. **集成到 LLM 客户端** - 支持 tool calling

#### Week 4: MCP Server
1. **创建 `mcp/server.py`** - MCP 协议实现
2. **标准化工具接口** - 注册和发现机制
3. **文档和测试** - API 文档和单元测试

### 阶段 3: 规划与多 Agent (3周)

#### Week 5-6: 规划器
1. **创建 `planner.py`** - CoT/ToT 规划器
2. **集成到 workflow** - 动态规划节点
3. **实现 Re-planning** - 错误恢复机制

#### Week 7: 多 Agent 架构
1. **创建 `agents/base.py`** - Agent 基类
2. **实现具体 Agents** - Fetcher, Scoring, Quality, Delivery
3. **创建 `orchestrator.py`** - 协调器

### 阶段 4: 集成与优化 (1周)

#### Week 8: 系统集成
1. **重构 `__init__.py`** - 新 workflow 组装
2. **性能优化** - 并行执行、缓存策略
3. **监控与可观测性** - Metrics, Logging

---

## 5. 关键文件清单

### 新增文件
```
ai-engine/src/
├── agent/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py              # Agent 基类
│   │   ├── fetcher_agent.py     # 抓取 Agent
│   │   ├── scoring_agent.py     # 评分 Agent
│   │   ├── quality_agent.py     # 质检 Agent (Reflection)
│   │   ├── summary_agent.py     # 摘要 Agent
│   │   ├── delivery_agent.py    # 交付 Agent
│   │   └── orchestrator.py      # 协调器
│   ├── planner.py               # 规划器 (CoT/ToT)
│   └── nodes_reflection.py      # 反思节点
├── tools/
│   └── __init__.py              # 工具层
├── mcp/
│   └── server.py                # MCP Server
└── memory/
    └── __init__.py              # 记忆管理

prompt/
└── quality_check_prompt.md      # 质量检查 Prompt
```

### 修改文件
```
ai-engine/src/
├── agent/
│   ├── __init__.py              # 重构 workflow 组装
│   ├── nodes.py                 # 兼容新状态
│   └── state.py                 # 增强状态定义
└── llm/
    └── __init__.py              # 支持 tool calling
```

---

## 6. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 重构范围过大 | 高 | 渐进式重构，每个阶段可独立交付 |
| Token 成本增加 | 中 | 智能缓存，按需调用 LLM |
| 延迟增加 | 中 | 并行执行，异步处理 |
| 向后兼容性 | 中 | 保留原有 API，逐步迁移 |
| 复杂度上升 | 中 | 完善文档，模块化设计 |

---

## 7. 验证方案

### 7.1 单元测试
```bash
# 测试记忆管理
pytest tests/memory/

# 测试工具层
pytest tests/tools/

# 测试 Agent
pytest tests/agents/
```

### 7.2 集成测试
```bash
# 端到端 workflow 测试
python -m tests.integration.test_full_workflow

# 性能基准测试
python -m tests.benchmark.latency_test
```

### 7.3 质量评估
```python
# 评估反思效果
quality_before = evaluate_summaries(summaries_old)
quality_after = evaluate_summaries(summaries_new)
assert quality_after.f1_score > quality_before.f1_score * 1.1

# 评估规划效果
completion_rate_before = 0.85
completion_rate_after = measure_task_completion()
assert completion_rate_after > 0.90
```

---

*文档生成时间: 2026-03-04*
*版本: v1.0*
