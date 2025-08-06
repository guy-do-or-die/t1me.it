# t1me.it 🔗

A modern link shortener with automatic screenshot previews and a clean React interface.

## Features

- **Link Shortening**: Generate short, memorable URLs
- **Screenshot Previews**: Automatic website screenshots for visual previews
- **Modern UI**: Clean React interface with Tailwind CSS
- **Fast API**: Python FastAPI backend with efficient caching
- **Docker Ready**: Containerized for easy deployment

## Quick Start

### Development

1. **Backend (Python FastAPI)**:
```bash
poetry install
poetry run python run.py
```

2. **Frontend (React + Vite)**:
```bash
cd app
bun install
bun dev
```

### Docker

```bash
docker-compose up -d
```

## API Endpoints

- `POST /api/links` - Create short link
- `GET /api/links/{short_id}` - Get link details
- `GET /{short_id}` - Redirect to original URL
- `GET /api/screenshot` - Generate website screenshot

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Backend**: Python, FastAPI, Playwright
- **Storage**: JSON file-based (easily extensible to database)
- **Deployment**: Docker, Docker Compose

## License

MIT License
