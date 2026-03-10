# TechNews Web App

Zero-dependency desktop web client for the existing `api-server`.

## Features

- Today feed with archive day pagination
- Favorites synced with authenticated user state
- Profile page for API base URL and preference editing
- Article detail panel with DeepSearch report rendering
- Nginx same-origin reverse proxy for `/api`

## Run with Docker Compose

```bash
docker compose up -d --build
```

Open `http://localhost:80`.
