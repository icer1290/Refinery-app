# Docker 运行调试指南

本文档记录了 Tech News Monorepo 项目的 Docker 环境运行和调试流程。

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                          │
├─────────────────────────────────────────────────────────────┤
│  technews-postgres   │ PostgreSQL 16  │ 端口 5432 (内部)    │
│  technews-qdrant     │ Qdrant        │ 端口 6333 (内部)    │
│  technews-ai-engine  │ FastAPI       │ 端口 8000 (内部)    │
│  technews-api-server │ Spring Boot   │ 端口 8080 (外部)    │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 启动所有服务

```bash
# 启动所有容器（后台运行）
docker-compose up -d

# 查看容器状态
docker-compose ps
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker logs technews-ai-engine
docker logs technews-api-server
docker logs technews-qdrant
docker logs technews-postgres

# 实时跟踪日志
docker logs -f technews-ai-engine
```

### 停止服务

```bash
# 停止所有容器
docker-compose down

# 停止并删除数据卷（清除所有数据）
docker-compose down -v
```

## 数据生成脚本

### 运行新闻数据生成脚本

该脚本执行完整的数据流程但不发送邮件：
1. 数据摄入（从 RSS feeds 抓取并存入 Qdrant）
2. Agent 工作流（fetch_data → scoring → deep_extraction → summarize）
3. 保存结果到文件

```bash
# 在容器内运行
docker exec -it technews-ai-engine python scripts/generate_news_data.py
```

### 查看输出文件

输出文件在容器内的 `/app/output/` 目录：

```bash
# 拷贝输出文件到本地
docker cp technews-ai-engine:/app/output/. ./ai-engine/output/

# 查看 HTML 预览
open ./ai-engine/output/news_preview_*.html

# 查看 JSON 数据
cat ./ai-engine/output/news_data_*.json | jq .
```

### 输出文件说明

| 文件 | 说明 |
|------|------|
| `news_data_YYYYMMDD_HHMMSS.json` | 完整 JSON 数据（包含文章、摘要、错误日志） |
| `news_preview_YYYYMMDD_HHMMSS.html` | 简易 HTML 预览页面 |

## 常用命令速查

### 容器管理

| 操作 | 命令 |
|------|------|
| 启动所有容器 | `docker-compose up -d` |
| 停止所有容器 | `docker-compose down` |
| 重启特定服务 | `docker-compose restart ai-engine` |
| 查看容器状态 | `docker-compose ps` |
| 查看容器资源使用 | `docker stats` |

### 进入容器

```bash
# 进入 ai-engine 容器交互模式
docker exec -it technews-ai-engine /bin/bash

# 进入 postgres 容器
docker exec -it technews-postgres /bin/bash

# 连接 PostgreSQL 数据库
docker exec -it technews-postgres psql -U postgres -d technews
```

### 文件操作

```bash
# 从容器拷贝文件到本地
docker cp technews-ai-engine:/app/output/. ./ai-engine/output/

# 从本地拷贝文件到容器
docker cp ./local_file.txt technews-ai-engine:/app/
```

### 镜像管理

```bash
# 重建特定服务镜像
docker-compose build ai-engine

# 重建所有镜像（不使用缓存）
docker-compose build --no-cache

# 重建并启动
docker-compose up -d --build
```

## 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| API Server | http://localhost:8080 | Spring Boot REST API |
| API Swagger | http://localhost:8080/swagger-ui.html | API 文档 |
| AI Engine API | http://localhost:8000 (内部) | FastAPI 服务 |
| AI Engine Docs | http://localhost:8000/docs (需端口映射) | FastAPI 文档 |
| Qdrant Dashboard | http://localhost:6333/dashboard (需端口映射) | 向量数据库管理 |

## 环境变量

### ai-engine

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `QWEN_API_KEY` | 通义千问 API 密钥 | 必填 |
| `QDRANT_URL` | Qdrant 服务地址 | `http://qdrant:6333` |
| `QDRANT_COLLECTION_NAME` | Qdrant 集合名称 | `tech_news` |

### api-server

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SPRING_DATASOURCE_URL` | PostgreSQL 连接地址 | `jdbc:postgresql://postgres:5432/technews` |
| `SPRING_DATASOURCE_USERNAME` | 数据库用户名 | `postgres` |
| `SPRING_DATASOURCE_PASSWORD` | 数据库密码 | `postgres` |
| `AI_ENGINE_URL` | AI Engine 服务地址 | `http://ai-engine:8000` |
| `JWT_SECRET` | JWT 签名密钥 | 必填 |

## 故障排查

### 容器无法启动

```bash
# 查看容器日志
docker-compose logs ai-engine

# 检查容器状态
docker-compose ps

# 检查网络
docker network ls
docker network inspect monorepo_default
```

### Qdrant 连接失败

```bash
# 检查 Qdrant 是否运行
docker exec -it technews-ai-engine curl http://qdrant:6333/collections

# 查看 Qdrant 日志
docker logs technews-qdrant
```

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否健康
docker exec -it technews-postgres pg_isready -U postgres

# 连接数据库测试
docker exec -it technews-postgres psql -U postgres -d technews -c "SELECT 1;"
```

### 脚本执行失败

```bash
# 进入容器检查文件
docker exec -it technews-ai-engine ls -la /app/scripts/

# 检查 Python 环境
docker exec -it technews-ai-engine python --version

# 手动测试导入
docker exec -it technews-ai-engine python -c "from src.pipeline.ingest_and_store import fetch_all_data; print('OK')"
```

## 重建镜像

当 Dockerfile 或依赖变更时，需要重建镜像：

```bash
# 重建 ai-engine 镜像
docker-compose build ai-engine

# 重启服务
docker-compose up -d ai-engine

# 或者一步完成
docker-compose up -d --build ai-engine
```

## 数据持久化

数据存储在 Docker volumes 中：

```bash
# 查看数据卷
docker volume ls

# 查看数据卷详情
docker volume inspect monorepo_postgres_data
docker volume inspect monorepo_qdrant_data

# 清除所有数据（谨慎操作）
docker-compose down -v
```

## 开发调试模式

### 本地运行 ai-engine（推荐开发调试）

```bash
cd ai-engine

# 激活虚拟环境
source .venv/bin/activate

# 配置环境变量（使用本地 Qdrant）
export QDRANT_URL=http://localhost:6333

# 运行 FastAPI 服务
uvicorn src.api.main:app --reload --port 8000

# 运行数据生成脚本
python scripts/generate_news_data.py
```

### 只启动基础设施

```bash
# 只启动 PostgreSQL 和 Qdrant
docker-compose up -d postgres qdrant

# 本地运行 ai-engine
cd ai-engine
export QDRANT_URL=http://localhost:6333
source .venv/bin/activate
python scripts/generate_news_data.py
```

## 注意事项

1. **脚本运行时机**：数据生成脚本需要在 Docker 容器启动后运行，因为它依赖 Qdrant 服务
2. **输出文件位置**：容器内的输出文件在 `/app/output/`，需要使用 `docker cp` 拷贝到本地查看
3. **环境变量**：确保 `.env` 文件或环境变量中配置了 `QWEN_API_KEY`
4. **网络隔离**：容器间使用 Docker 内部网络通信，ai-engine 和 qdrant 不对外暴露端口