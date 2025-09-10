# Docker Quick Start Guide

This document provides instructions for running the Alice AI Assignment Tracker using Docker instead of the batch files.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (usually included with Docker Desktop)

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Start the application:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - API Documentation: http://localhost:8001/docs

3. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Option 2: Run in Background (Detached Mode)

1. **Start services in background:**
   ```bash
   docker-compose up -d --build
   ```

2. **View logs:**
   ```bash
   # All services
   docker-compose logs -f
   
   # Specific service
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

3. **Stop background services:**
   ```bash
   docker-compose down
   ```

## Development Commands

### Rebuild containers after code changes:
```bash
docker-compose up --build
```

### Clean rebuild (remove cache):
```bash
docker-compose build --no-cache
docker-compose up
```

### View running containers:
```bash
docker-compose ps
```

### Access container shell:
```bash
# Backend container
docker-compose exec backend bash

# Frontend container
docker-compose exec frontend sh
```

## Troubleshooting

### Port conflicts:
If ports 3000 or 8001 are already in use, modify the ports in `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Change 3000 to 3001
  - "8002:8001"  # Change 8001 to 8002
```

### Database persistence:
The SQLite database is persisted in the `./backend/assignments.db` file on your host machine.

### Clean restart:
```bash
docker-compose down
docker-compose up --build
```

## Migration from Batch Files

Instead of using:
- `start_app.bat` → Use `docker-compose up`
- `stop_app.bat` → Use `docker-compose down`

The Docker setup provides the same functionality with better isolation and consistency across different environments.
