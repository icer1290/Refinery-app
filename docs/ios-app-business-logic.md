# iOS App 业务逻辑文档

本文档详细说明 iOS App 在两个后端服务（API Server 和 AI Engine）启动后的各项业务逻辑。

## 系统架构概览

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   iOS App       │ ──→  │  API Server     │ ──→  │   AI Engine     │
│  (SwiftUI)      │      │  (Spring Boot)  │      │   (FastAPI)     │
│  Port: N/A      │      │  Port: 8080     │      │  Port: 8000     │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                │                        │
                                ▼                        ▼
                         ┌─────────────────┐      ┌─────────────────┐
                         │   PostgreSQL    │      │    Qdrant       │
                         │   (用户数据)     │      │  (向量数据库)    │
                         └─────────────────┘      └─────────────────┘
```

### 服务职责

| 服务 | 端口 | 职责 |
|------|------|------|
| iOS App | - | 用户界面，SwiftUI 实现 |
| API Server | 8080 | BFF (Backend for Frontend)，用户认证，业务逻辑 |
| AI Engine | 8000 | 新闻采集、AI 评分、内容摘要、向量存储 |
| PostgreSQL | 5432 | 用户数据、新闻缓存、收藏关系 |
| Qdrant | 6333 | 向量数据库，语义搜索 |

---

## 业务逻辑详解

### 1. 用户认证流程

#### 1.1 用户注册

**时序图：**

```
iOS App                          API Server                    PostgreSQL
   │                                │                              │
   │ POST /api/auth/register        │                              │
   │ {email, password, nickname}    │                              │
   │───────────────────────────────→│                              │
   │                                │ 检查邮箱是否存在               │
   │                                │─────────────────────────────→│
   │                                │     创建用户记录               │
   │                                │─────────────────────────────→│
   │                                │ 生成 JWT Token               │
   │   {token, userId, email}       │                              │
   │←───────────────────────────────│                              │
   │                                │                              │
   │ 保存 token 到 UserDefaults     │                              │
```

**API 端点：**
- `POST /api/auth/register`

**请求体：**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "nickname": "John Doe"
}
```

**响应：**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "userId": 1,
    "email": "user@example.com"
  }
}
```

**客户端处理：**
- 保存 `token`、`userId`、`email` 到 `UserDefaults`
- 更新 `AuthViewModel.isAuthenticated = true`

---

#### 1.2 用户登录

**时序图：**

```
iOS App                          API Server                    PostgreSQL
   │                                │                              │
   │ POST /api/auth/login           │                              │
   │ {email, password}              │                              │
   │───────────────────────────────→│                              │
   │                                │ 验证密码                     │
   │                                │─────────────────────────────→│
   │                                │ 生成 JWT Token               │
   │   {token, userId, email}       │                              │
   │←───────────────────────────────│                              │
```

**API 端点：**
- `POST /api/auth/login`

**请求体：**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应：** 同注册

---

#### 1.3 登出

**客户端处理：**
- 调用 `AuthService.logout()`
- 清除 `UserDefaults` 中的认证信息
- 更新 `AuthViewModel.isAuthenticated = false`

---

### 2. 今日新闻浏览

**时序图：**

```
iOS App                    API Server               AI Engine              Qdrant          PostgreSQL
   │                           │                        │                    │                 │
   │ GET /api/news/today       │                        │                    │                 │
   │ Authorization: Bearer xxx │                        │                    │                 │
   │──────────────────────────→│                        │                    │                 │
   │                           │ 查询今日新闻            │                    │                 │
   │                           │────────────────────────────────────────────────────────────→│
   │                           │                        │                    │     结果为空?   │
   │                           │                        │                    │         ↓       │
   │                           │ GET /internal/news/today                    │                 │
   │                           │───────────────────────→│                    │                 │
   │                           │                        │ fetch_today_news() │                 │
   │                           │                        │───────────────────→│                 │
   │                           │                        │     news records   │                 │
   │                           │                        │←───────────────────│                 │
   │                           │     news list          │                    │                 │
   │                           │←───────────────────────│                    │                 │
   │                           │ 保存到 PostgreSQL       │                    │                 │
   │                           │────────────────────────────────────────────────────────────→│
   │                           │ 查询用户收藏状态        │                    │                 │
   │                           │────────────────────────────────────────────────────────────→│
   │   NewsResponse[]          │                        │                    │                 │
   │   (含 isFavorite 字段)     │                        │                    │                 │
   │←──────────────────────────│                        │                    │                 │
```

**API 端点：**
- `GET /api/news/today`

**核心逻辑** (`NewsService.java:28-41`):

1. **缓存优先策略**：先查询本地 PostgreSQL
2. **数据源回退**：如果为空，调用 AI Engine 从 Qdrant 获取
3. **数据同步**：将获取的数据保存到 PostgreSQL
4. **用户状态**：如果用户已登录，附加收藏状态 (`isFavorite`)

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "OpenAI Announces GPT-5",
      "translatedTitle": "OpenAI 发布 GPT-5",
      "url": "https://example.com/news/1",
      "source": "TechCrunch",
      "category": "AI & Machine Learning",
      "score": 150,
      "llmScore": 8.5,
      "finalScore": 0.85,
      "summary": "OpenAI has announced its latest model...",
      "publishedDate": "2026-02-28",
      "isFavorite": false
    }
  ]
}
```

---

### 3. 新闻归档浏览

**时序图：**

```
iOS App                          API Server                    PostgreSQL
   │                                │                              │
   │ GET /api/news/archive          │                              │
   │ ?startDate=2026-02-01          │                              │
   │ &endDate=2026-02-28            │                              │
   │───────────────────────────────→│                              │
   │                                │ 按日期范围查询                 │
   │                                │ ORDER BY publishedDate DESC,  │
   │                                │ finalScore DESC               │
   │                                │─────────────────────────────→│
   │   NewsResponse[]               │                              │
   │←───────────────────────────────│                              │
```

**API 端点：**
- `GET /api/news/archive?startDate=2026-02-01&endDate=2026-02-28`

**参数：**
- `startDate` (可选): ISO 日期格式，默认一个月前
- `endDate` (可选): ISO 日期格式，默认今天

**排序规则：**
- 主排序：`publishedDate DESC`
- 次排序：`finalScore DESC`

---

### 4. 新闻详情

**时序图：**

```
iOS App                          API Server                    PostgreSQL
   │                                │                              │
   │ GET /api/news/{id}             │                              │
   │───────────────────────────────→│                              │
   │                                │ findById(id)                 │
   │                                │─────────────────────────────→│
   │                                │ 检查用户收藏状态               │
   │   NewsResponse                 │                              │
   │   (含完整 summary)             │                              │
   │←───────────────────────────────│                              │
```

**API 端点：**
- `GET /api/news/{id}`

**说明：**
- 返回完整的新闻详情，包括完整摘要
- 如果用户已登录，包含 `isFavorite` 字段

---

### 5. 收藏功能

#### 5.1 添加收藏

**时序图：**

```
iOS App                          API Server                    PostgreSQL
   │                                │                              │
   │ POST /api/news/{id}/favorite   │                              │
   │ Authorization: Bearer xxx      │                              │
   │───────────────────────────────→│                              │
   │                                │ 解析 JWT 获取 userId          │
   │                                │ 检查是否已收藏                 │
   │                                │ 创建 Favorite 记录             │
   │                                │─────────────────────────────→│
   │   "Added to favorites"         │                              │
   │←───────────────────────────────│                              │
```

**API 端点：**
- `POST /api/news/{id}/favorite`

**认证要求：** 需要 JWT Token

---

#### 5.2 取消收藏

**时序图：**

```
iOS App                          API Server                    PostgreSQL
   │                                │                              │
   │ DELETE /api/news/{id}/favorite │                              │
   │ Authorization: Bearer xxx      │                              │
   │───────────────────────────────→│                              │
   │                                │ 删除 Favorite 记录             │
   │                                │─────────────────────────────→│
   │   "Removed from favorites"     │                              │
   │←───────────────────────────────│                              │
```

**API 端点：**
- `DELETE /api/news/{id}/favorite`

---

#### 5.3 查看收藏列表

**时序图：**

```
iOS App                          API Server                    PostgreSQL
   │                                │                              │
   │ GET /api/user/favorites        │                              │
   │ Authorization: Bearer xxx      │                              │
   │───────────────────────────────→│                              │
   │                                │ 查询用户收藏                   │
   │                                │ JOIN News 表                  │
   │                                │─────────────────────────────→│
   │   NewsResponse[]               │                              │
   │   (用户收藏的新闻)              │                              │
   │←───────────────────────────────│                              │
```

**API 端点：**
- `GET /api/user/favorites`

---

### 6. 用户偏好设置

#### 6.1 获取偏好设置

**API 端点：**
- `GET /api/user/preferences`

**响应示例：**
```json
{
  "success": true,
  "data": {
    "categories": ["AI & Machine Learning", "Cloud & DevOps"],
    "keywords": ["LLM", "Kubernetes"]
  }
}
```

---

#### 6.2 更新偏好设置

**时序图：**

```
iOS App                          API Server                    PostgreSQL
   │                                │                              │
   │ PUT /api/user/preferences      │                              │
   │ {categories: ["AI", "Cloud"]}  │                              │
   │───────────────────────────────→│                              │
   │                                │ 更新偏好设置                   │
   │                                │─────────────────────────────→│
   │   "Preferences updated"        │                              │
   │←───────────────────────────────│                              │
```

**API 端点：**
- `PUT /api/user/preferences`

**请求体：**
```json
{
  "categories": ["AI & Machine Learning", "Cloud & DevOps"],
  "keywords": ["LLM", "Kubernetes"]
}
```

---

### 7. 可用日期查询

**时序图：**

```
iOS App                          API Server                    PostgreSQL
   │                                │                              │
   │ GET /api/news/dates            │                              │
   │───────────────────────────────→│                              │
   │                                │ SELECT DISTINCT publishedDate │
   │                                │─────────────────────────────→│
   │   ["2026-02-28", "2026-02-27"] │                              │
   │←───────────────────────────────│                              │
```

**API 端点：**
- `GET /api/news/dates`

**用途：**
- 用于归档页面的日历选择器
- 显示有新闻数据的日期

---

## 数据流总结

| 功能 | iOS 调用 | API Server 处理 | AI Engine 交互 | 认证要求 |
|------|----------|-----------------|----------------|----------|
| 登录 | `POST /api/auth/login` | JWT 生成/验证 | 无 | 无 |
| 注册 | `POST /api/auth/register` | 用户创建/JWT | 无 | 无 |
| 今日新闻 | `GET /api/news/today` | 缓存优先策略 | 数据源 (Qdrant) | 可选 |
| 归档新闻 | `GET /api/news/archive` | 直接查询 DB | 无 | 可选 |
| 新闻详情 | `GET /api/news/{id}` | 直接查询 DB | 无 | 可选 |
| 添加收藏 | `POST /api/news/{id}/favorite` | 关联用户 | 无 | **必须** |
| 取消收藏 | `DELETE /api/news/{id}/favorite` | 删除关联 | 无 | **必须** |
| 收藏列表 | `GET /api/user/favorites` | 用户专属数据 | 无 | **必须** |
| 获取偏好 | `GET /api/user/preferences` | 用户专属数据 | 无 | **必须** |
| 更新偏好 | `PUT /api/user/preferences` | 更新偏好 | 无 | **必须** |
| 可用日期 | `GET /api/news/dates` | 元数据查询 | 无 | 无 |

---

## 核心设计原则

### 1. BFF 模式 (Backend for Frontend)

API Server 作为 iOS App 的唯一后端入口，统一处理：
- 请求路由
- 数据聚合
- 格式转换
- 认证授权

### 2. 缓存优先策略

```
请求 → PostgreSQL (缓存) → 命中 → 返回
                         → 未命中 → AI Engine (Qdrant) → 缓存到 PostgreSQL → 返回
```

**优势：**
- 减少对 AI Engine 的直接请求
- 降低响应延迟
- 提高系统稳定性

### 3. JWT 无状态认证

- Token 存储在客户端 `UserDefaults`
- 每次请求携带 `Authorization: Bearer <token>`
- 服务端无需存储 Session

### 4. AI Engine 作为数据源

AI Engine 负责：
- 新闻采集 (RSS, Hacker News, Product Hunt)
- AI 评分 (LLM-based scoring)
- 内容摘要 (tiered summarization)
- 向量存储 (Qdrant for semantic search)

---

## iOS App 界面结构

```
ContentView (TabView)
├── NewsListView (Tab 0: "Today")
│   └── NewsDetailView
├── ArchiveView (Tab 1: "Archive")
│   ├── DatePicker
│   └── NewsDetailView
└── SettingsView (Tab 2: "Settings")
    ├── User Preferences
    ├── Favorites List
    └── Logout Button
```

---

## 错误处理

### API 错误响应格式

```json
{
  "success": false,
  "message": "Resource not found",
  "data": null
}
```

### iOS 客户端错误类型

```swift
enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case decodingError
    case unauthorized
}
```

---

## 相关文件索引

### iOS App 关键文件

| 文件 | 职责 |
|------|------|
| `Services/APIClient.swift` | 网络请求基础类，JWT 管理 |
| `Services/AuthService.swift` | 认证服务 |
| `Services/NewsService.swift` | 新闻相关 API |
| `ViewModels/AuthViewModel.swift` | 认证状态管理 |
| `ViewModels/NewsViewModel.swift` | 新闻数据管理 |
| `Utils/Constants.swift` | API 端点配置 |

### API Server 关键文件

| 文件 | 职责 |
|------|------|
| `controller/AuthController.java` | 认证端点 |
| `controller/NewsController.java` | 新闻端点 |
| `controller/UserController.java` | 用户偏好端点 |
| `service/NewsService.java` | 新闻业务逻辑 |
| `service/AiEngineClient.java` | AI Engine 客户端 |

### AI Engine 关键文件

| 文件 | 职责 |
|------|------|
| `api/routes/news.py` | 新闻 API 端点 |
| `api/main.py` | FastAPI 应用配置 |