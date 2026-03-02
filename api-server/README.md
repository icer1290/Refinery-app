# Tech News API Server

Spring Boot backend service for the Tech News application.

## Tech Stack

- Java 17
- Spring Boot 3.2.3
- Spring Security + JWT
- Spring Data JPA
- PostgreSQL
- SpringDoc OpenAPI

## Quick Start

### Prerequisites

- Java 17+
- Maven 3.6+
- PostgreSQL 14+

### Database Setup

```sql
CREATE DATABASE technews;
```

### Configuration

Update `src/main/resources/application.yml` with your database credentials:

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/technews
    username: your_username
    password: your_password
```

### Run

```bash
# Development
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev

# Production
./mvnw clean package
java -jar target/api-server-1.0.0-SNAPSHOT.jar
```

### API Documentation

Access Swagger UI at: http://localhost:8080/swagger-ui.html

## API Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/auth/register` | POST | Register new user | No |
| `/api/auth/login` | POST | User login | No |
| `/api/news/today` | GET | Get today's news | Optional |
| `/api/news/archive` | GET | Get archived news | Optional |
| `/api/news/{id}` | GET | Get news by ID | Optional |
| `/api/news/{id}/favorite` | POST | Add to favorites | Yes |
| `/api/news/{id}/favorite` | DELETE | Remove from favorites | Yes |
| `/api/user/preferences` | GET | Get user preferences | Yes |
| `/api/user/preferences` | PUT | Update preferences | Yes |
| `/api/user/favorites` | GET | Get user favorites | Yes |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET` | JWT signing key | (change in production) |
| `AI_ENGINE_URL` | AI Engine base URL | `http://localhost:8000` |

## Project Structure

```
src/main/java/com/technews/
├── TechNewsApplication.java   # Main entry point
├── config/                    # Configuration classes
│   ├── CorsConfig.java
│   ├── JwtConfig.java
│   ├── JwtAuthenticationFilter.java
│   └── SecurityConfig.java
├── controller/                # REST controllers
│   ├── AuthController.java
│   ├── NewsController.java
│   └── UserController.java
├── service/                   # Business logic
│   ├── AuthService.java
│   ├── CustomUserDetailsService.java
│   ├── NewsService.java
│   ├── UserService.java
│   └── AiEngineClient.java
├── repository/                # Data access
│   ├── UserRepository.java
│   ├── NewsRepository.java
│   ├── UserPreferenceRepository.java
│   └── FavoriteRepository.java
├── entity/                    # JPA entities
│   ├── User.java
│   ├── News.java
│   ├── UserPreference.java
│   └── Favorite.java
├── dto/                       # Data transfer objects
│   ├── request/
│   └── response/
└── exception/                 # Exception handling
```
