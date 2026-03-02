# Refinery - 智能科技新闻日报系统

> 自动化获取、智能分析和分发科技资讯的完整解决方案

Refinery 是一个基于 LangGraph 的智能科技新闻日报系统，从多个权威来源获取最新资讯，通过 AI 进行语义去重、评分分级、深度摘要，最终生成精美的日报并通过邮件自动推送。

## 核心特性

- **多源数据采集**：整合 15+ 权威科技媒体的 RSS 订阅源
- **智能语义去重**：基于向量相似度自动识别和过滤重复内容
- **AI 评分分级**：使用 LLM 对新闻内容进行智能评分和排序
- **分级摘要生成**：Top 5 深度解读 + Top 10 精简简报的差异化输出
- **自动化工作流**：基于 LangGraph 构建的端到端自动化流程
- **邮件自动推送**：每日定时发送精美 HTML 邮件日报

## 技术架构

```
数据源 -> 去重入库 -> 评分分级 -> 深度提取 -> 摘要生成 -> 邮件推送
```

### 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| **核心框架** | LangGraph | 工作流编排和状态管理 |
| **向量数据库** | Qdrant | 新闻存储和语义检索 |
| **AI 模型** | 通义千问 API | 内容分析、评分和摘要生成 |
| **HTTP 客户端** | requests / httpx | API 调用和网页抓取 |
| **RSS 解析** | feedparser | 订阅源数据解析 |
| **内容提取** | trafilatura | 深度正文内容提取 |
| **模板引擎** | Jinja2 | HTML 邮件模板渲染 |
| **容器化** | Docker Compose | Qdrant 服务部署 |

## 快速开始

### 环境要求

- Python 3.12+
- Docker 和 Docker Compose
- 通义千问 API Key

### 安装步骤

1. **克隆仓库**

   ```bash
   git clone https://github.com/yourusername/Refinery.git
   cd Refinery
   ```

2. **创建虚拟环境并安装依赖**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或 .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **配置环境变量**

   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填写必要的配置
   ```

   必需的环境变量：

   ```bash
   QWEN_API_KEY=your_qwen_api_key_here
   QWEN_EMBEDDING_MODEL=text-embedding-v4
   QWEN_CHAT_MODEL=qwen3-30b-a3b-instruct-2507
   QDRANT_URL=http://localhost:6333
   QDRANT_COLLECTION_NAME=tech_news
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASS=your_app_password
   NEWSLETTER_RECIPIENT=recipient@example.com
   ```

4. **启动 Qdrant 服务**

   ```bash
   docker compose up -d
   ```

### 运行项目

#### 方式一：完整工作流

```bash
# 1. 数据采集与入库
python -m src.pipeline.ingest_and_store

# 2. 运行 Agent 生成日报
python -m src.agent
```

#### 方式二：单节点调试

```bash
# 仅运行特定节点
python -m src.agent --node fetch_data
python -m src.agent --node scoring
python -m src.agent --node deep_extraction
python -m src.agent --node summarize
python -m src.agent --node delivery
```

## 工作流详解

### 1. 数据获取 (fetch_data)

从 Qdrant 向量数据库中获取当日（UTC+8 时间）所有已入库的新闻元数据。

### 2. 智能评分 (scoring)

- 使用 LLM 对新闻标题和简介进行评分（0-10 分）
- 计算加权得分：`Final_Score = (原始热度/Batch最大热度) * 0.3 + (LLM打分/10) * 0.7`
- 按得分排序，Top 30 进入候选池，Top 15 进入深度处理流程

### 3. 深度提取 (deep_extraction)

- 使用 trafilatura 并发抓取 Top 15 新闻的正文内容
- 限制并发数为 5，单条请求超时 30 秒
- 提取失败的新闻从候选池自动补齐

### 4. 摘要生成 (summarize)

采用分级摘要策略：

- **Top 1-5**：生成深度解读（包含主编视角与深度洞察）
- **Top 6-15**：生成精简简报（仅保留钩子句子与核心事实）

### 5. 邮件交付 (delivery)

- 使用 Jinja2 渲染精美 HTML 邮件模板
- 批量翻译新闻标题为中文
- 通过 SMTP 发送到指定邮箱
- 自动保存 HTML 文件到 `output/` 目录

## 项目结构

```
Refinery/
├── src/
│   ├── agent/                    # Agent 工作流系统
│   │   ├── __init__.py          # 工作流定义
│   │   ├── __main__.py          # 入口文件
│   │   ├── nodes.py             # 节点实现（5 个核心节点）
│   │   └── state.py             # 状态定义
│   ├── ingestion/                # 数据采集模块
│   │   ├── hacker_news.py       # Hacker News 数据获取
│   │   ├── product_hunt.py      # Product Hunt 数据获取
│   │   └── rss_feeds.py         # RSS 订阅源采集
│   ├── preprocessing/            # 数据预处理
│   │   └── semantic_dedup.py    # 语义去重
│   ├── vector_store/              # 向量数据库接口
│   │   └── __init__.py
│   ├── pipeline/                  # 数据处理管道
│   │   └── ingest_and_store.py  # 采集和存储流程
│   ├── embeddings/                # 嵌入模型
│   │   └── __init__.py
│   ├── extraction/                # 内容提取
│   │   └── __init__.py
│   ├── llm/                       # LLM 客户端
│   │   └── __init__.py
│   ├── prompt/                    # Prompt 模板
│   │   ├── email_template.html  # 邮件模板
│   │   ├── scoring_prompt.md    # 评分 Prompt
│   │   ├── summary_prompt.md    # 深度摘要 Prompt
│   │   └── simple_summary_prompt.md  # 精简摘要 Prompt
│   └── email_sender.py            # 邮件发送功能
├── .github/workflows/             # GitHub Actions 配置
│   └── daily_agent.yml          # 每日定时任务
├── output/                        # 输出目录（邮件 HTML）
├── qdrant_data/                   # Qdrant 数据持久化
├── checkpoints/                   # Agent 检查点
├── .env.example                   # 环境变量示例
├── .gitignore                     # Git 忽略配置
├── docker-compose.yml             # Docker Compose 配置
├── requirements.txt               # Python 依赖
└── README.md                      # 项目说明
```

## 自动化部署

### GitHub Actions

项目已配置 GitHub Actions 工作流，每天北京时间上午 8:00 自动运行：

```yaml
# 每天北京时间 8:00 (UTC 0:00) 运行
cron: '0 0 * * *'
```

配置步骤：

1. 在 GitHub 仓库中添加以下 Secrets：
   - `QWEN_API_KEY`：通义千问 API 密钥
   - `SMTP_USER`：发送邮件邮箱
   - `SMTP_PASS`：邮箱密码或应用密码
   - `NEWSLETTER_RECIPIENT`：收件人邮箱

2. 推送代码后，工作流自动触发

3. 也可在 GitHub Actions 页面手动触发

## 开发指南

### 添加新的 RSS 源

编辑 `src/ingestion/rss_feeds.py`，在 `RSS_FEEDS` 列表中添加新源：

```python
RSS_FEEDS = [
    {"name": "新源名称", "url": "https://example.com/feed"},
    # ... 其他源
]
```

### 自定义 Prompt 模板

所有 Prompt 模板位于 `src/prompt/` 目录：

- `scoring_prompt.md`：评分规则
- `summary_prompt.md`：深度摘要模板
- `simple_summary_prompt.md`：精简摘要模板
- `email_template.html`：邮件 HTML 模板

### 修改评分权重

编辑 `src/agent/nodes.py` 的 `scoring_node` 函数：

```python
# 默认权重：原始热度 30%，LLM 评分 70%
final_score = normalized_popularity * 0.3 + normalized_llm_score * 0.7
```

### 调整新闻数量

在 `src/agent/nodes.py` 中修改：

```python
# candidate_pool 数量（默认 Top 30）
top_30 = sorted_news[:30]

# deep_extraction 数量（默认 Top 15）
top_15 = sorted_news[:15]
```

## 环境变量说明

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `QWEN_API_KEY` | 是 | - | 通义千问 API 密钥 |
| `QWEN_EMBEDDING_MODEL` | 否 | `text-embedding-v4` | 嵌入模型 |
| `QWEN_CHAT_MODEL` | 否 | `qwen3-30b-a3b-instruct-2507` | 聊天模型 |
| `QDRANT_URL` | 否 | `http://localhost:6333` | Qdrant 服务地址 |
| `QDRANT_COLLECTION_NAME` | 否 | `tech_news` | Qdrant 集合名称 |
| `SMTP_HOST` | 是 | - | SMTP 服务器地址 |
| `SMTP_PORT` | 是 | - | SMTP 服务器端口 |
| `SMTP_USER` | 是 | - | 发件人邮箱 |
| `SMTP_PASS` | 是 | - | 邮箱密码或应用密码 |
| `NEWSLETTER_RECIPIENT` | 是 | - | 收件人邮箱 |

## 常见问题

### Q: 如何处理邮件发送失败？

A: 邮件发送失败时会自动保存 HTML 文件到 `output/` 目录，可直接查看或手动转发。

### Q: 如何调整运行频率？

A: 编辑 `.github/workflows/daily_agent.yml` 中的 `cron` 表达式。

### Q: Qdrant 数据丢失怎么办？

A: Qdrant 数据会持久化到 `qdrant_data/` 目录，确保该目录正确挂载。

### Q: 如何测试单个模块？

A: 使用 `python -m src.agent --node <节点名>` 测试单个节点。

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**Refinery** - 让科技资讯触手可及
