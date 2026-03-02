# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tech News Monorepo - A full-stack tech news aggregation platform with AI-powered content processing.

## Architecture

```
monorepo/
├── ai-engine/      # Python/LangGraph AI Engine (FastAPI) - port 8000
├── api-server/     # Spring Boot Backend Service - port 8080
└── tech-news-ios/  # SwiftUI iOS Application (iOS 16.0+)
```

## Development Commands

### Infrastructure

```bash
# Start PostgreSQL and Qdrant
docker-compose up -d
```

### AI Engine (Python)

```bash
cd ai-engine

# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env

# Run FastAPI server
uvicorn src.api.main:app --reload --port 8000

# Run full agent workflow
python -m src.agent

# Run single node (for testing)
python -m src.agent --node fetch_data
python -m src.agent --node scoring
python -m src.agent --node deep_extraction
python -m src.agent --node summarize
python -m src.agent --node delivery

# Data ingestion pipeline
python -m src.pipeline.ingest_and_store

# Run tests
pytest
```

### API Server (Java/Spring Boot)

```bash
cd api-server

# Development
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev

# Production build
./mvnw clean package
java -jar target/api-server-1.0.0-SNAPSHOT.jar

# Run tests
./mvnw test
```

### iOS App

```bash
cd tech-news-ios

# Generate Xcode project (requires xcodegen)
brew install xcodegen
xcodegen generate

# Build
xcodebuild -scheme TechNewsApp build

# Run tests
xcodebuild test -scheme TechNewsApp
```

## AI Engine Architecture

The AI engine uses LangGraph for workflow orchestration with 5 sequential nodes:

```
fetch_data → scoring → deep_extraction → summarize → delivery
```

- **fetch_data**: Retrieves news from Qdrant vector database
- **scoring**: LLM-based scoring (0-10) with weighted formula: `(popularity * 0.3) + (LLM_score * 0.7)`
- **deep_extraction**: Extracts full article content using trafilatura (Top 15 articles)
- **summarize**: Tiered summarization - Top 5 get deep analysis, Top 6-15 get brief summaries
- **delivery**: Generates HTML email and sends via SMTP

Key modules:
- `src/agent/` - LangGraph workflow definitions and nodes
- `src/ingestion/` - RSS feeds, Hacker News, Product Hunt ingestion
- `src/preprocessing/` - Semantic deduplication
- `src/vector_store/` - Qdrant interface
- `src/llm/` - Qwen API client
- `src/extraction/` - Content extraction with trafilatura
- `src/prompt/` - Prompt templates for scoring and summarization

## API Server Architecture

Spring Boot service with:
- JWT-based authentication via `SecurityConfig` and `JwtAuthenticationFilter`
- REST controllers: `AuthController`, `NewsController`, `UserController`
- `AiEngineClient` service for communicating with ai-engine
- JPA entities: User, News, UserPreference, Favorite

## Required Environment Variables

### ai-engine (.env)
- `QWEN_API_KEY` - Tongyi Qianwen API key
- `QDRANT_URL` - Qdrant server URL (default: http://localhost:6333)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` - Email delivery
- `NEWSLETTER_RECIPIENT` - Newsletter recipient email

### api-server (application.yml)
- `JWT_SECRET` - JWT signing key
- `AI_ENGINE_URL` - AI Engine base URL (default: http://localhost:8000)

## Service URLs

- AI Engine API docs: http://localhost:8000/docs
- API Server Swagger: http://localhost:8080/swagger-ui.html
- Qdrant dashboard: http://localhost:6333/dashboard