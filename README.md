# Tech News Monorepo

A full-stack tech news aggregation platform with AI-powered content processing.

## Architecture

```
monorepo/
├── ai-engine/      # Python/LangGraph AI Engine (FastAPI)
├── api-server/     # Spring Boot Backend Service
└── tech-news-ios/  # SwiftUI iOS Application
```

## Components

| Service | Port | Description |
|---------|------|-------------|
| ai-engine | 8000 | News ingestion, scoring, summarization |
| api-server | 8080 | Business API, user management, news serving |
| postgresql | 5432 | Primary database |
| qdrant | 6333 | Vector database for semantic search |

## Quick Start

### Prerequisites

- Python 3.12+
- Java 17+
- Node.js 18+ (for tools)
- Docker & Docker Compose
- PostgreSQL 14+

### 1. Start Infrastructure

```bash
# Start PostgreSQL and Qdrant
docker-compose up -d
```

### 2. Start AI Engine

```bash
cd ai-engine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start FastAPI server
uvicorn src.api.main:app --reload --port 8000
```

### 3. Start API Server

```bash
cd api-server

# Build and run
./mvnw spring-boot:run

# Or with dev profile
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev
```

### 4. Start iOS App

```bash
cd tech-news-ios

# Generate Xcode project (requires xcodegen)
brew install xcodegen
xcodegen generate

# Open in Xcode
open TechNewsApp.xcodeproj
```

## Documentation

- [iOS App 业务逻辑文档](docs/ios-app-business-logic.md) - 详细的业务流程和 API 调用说明

## API Documentation

- **AI Engine**: http://localhost:8000/docs
- **API Server**: http://localhost:8080/swagger-ui.html

## Development

### Database Migrations

The API server uses Hibernate's `ddl-auto=update` for development. For production, consider using Flyway or Liquibase.

### Environment Variables

#### ai-engine (.env)
```bash
QWEN_API_KEY=your_api_key
QDRANT_URL=http://localhost:6333
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASS=your_password
```

#### api-server (application.yml)
```yaml
JWT_SECRET: your-256-bit-secret
AI_ENGINE_URL: http://localhost:8000
```

## Testing

### AI Engine
```bash
cd ai-engine
pytest
```

### API Server
```bash
cd api-server
./mvnw test
```

### iOS App
```bash
cd tech-news-ios
xcodebuild test -scheme TechNewsApp
```

## Deployment

Each service can be deployed independently:

- **ai-engine**: Containerize with Docker, deploy to any container service
- **api-server**: Build JAR, deploy to Kubernetes, ECS, or traditional servers
- **tech-news-ios**: Submit to App Store via Xcode

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## License

MIT License
