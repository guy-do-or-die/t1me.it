# shot.in 📸

A universal, timecode-based video screenshot microservice that generates precise, high-resolution preview images from any public video URL at a specified timestamp.

## 🌟 Features

- **Precise Timestamps**: Capture exact frames at specified timestamps using headless browser rendering
- **Universal Support**: Works with YouTube, Vimeo, Twitch, direct video files, and more
- **High Performance**: Multi-layer caching (local disk + Redis) for optimal response times
- **Scalable**: Dockerized and ready for deployment on any platform
- **RESTful API**: Simple HTTP endpoints for easy integration
- **Image Optimization**: Automatic resizing and compression for web delivery

## 🚀 Quick Start

### Local Development

1. **Clone and setup**:
```bash
git clone <repository-url>
cd shot.in
cp .env.example .env
```

2. **Install dependencies**:
```bash
poetry install
poetry run playwright install chromium
```

3. **Run the service**:
```bash
poetry run python main.py
# or
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The service will be available at `http://localhost:8000`

### Docker Deployment

```bash
# Build and run with Docker Compose (includes Redis)
docker-compose up -d

# Or build and run standalone
docker build -t shot-in .
docker run -p 8000:8000 shot-in
```

## 📖 API Documentation

### Generate Screenshot

```http
GET /screenshot?url={video_url}&t={timestamp}&w={width}&h={height}
```

**Parameters:**
- `url` (required): Public video URL to capture from
- `t` (optional): Timestamp in seconds (default: 0)
- `w` (optional): Screenshot width in pixels (default: 1280, max: 1920)
- `h` (optional): Screenshot height in pixels (default: 720, max: 1080)

**Example:**
```bash
curl "http://localhost:8000/screenshot?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30&w=1280&h=720"
```

### Other Endpoints

- `GET /` - Service information and available endpoints
- `GET /health` - Health check and system status
- `DELETE /cache/{cache_key}` - Clear specific cached screenshot
- `DELETE /cache` - Clear all cached screenshots

## 🔧 Configuration

Environment variables (see `.env.example`):

- `REDIS_URL`: Redis connection URL (optional, enables distributed caching)
- `MAX_WIDTH`: Maximum screenshot width (default: 1920)
- `MAX_HEIGHT`: Maximum screenshot height (default: 1080)
- `CACHE_EXPIRY`: Cache expiration time in seconds (default: 86400)

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Client App    │───▶│   shot.in    │───▶│  Playwright │
└─────────────────┘    │   FastAPI    │    │   Browser   │
                       └──────────────┘    └─────────────┘
                              │
                              ▼
                       ┌──────────────┐    ┌─────────────┐
                       │    Cache     │───▶│    Redis    │
                       │  (Local +    │    │ (Optional)  │
                       │   Redis)     │    └─────────────┘
                       └──────────────┘
```

## 🎯 Use Cases

- **Social Media**: Generate thumbnails for timestamped video moments
- **Documentation**: Embed precise video frames in blogs and docs
- **Education**: Create visual references for specific video content
- **Media Analysis**: Extract frames for research and commentary
- **OpenGraph Previews**: Dynamic video previews for social sharing

## ⚖️ Legal Considerations

shot.in operates within fair use guidelines:
- Only captures single frames, not full video content
- Renders publicly available content as viewed in a browser
- Respects platform terms of service and rate limits
- Does not download or redistribute complete videos

## 🚀 Deployment Options

### Cloud Platforms
- **Fly.io**: `flyctl launch`
- **Railway**: Connect GitHub repo
- **Render**: Docker deployment
- **Heroku**: Container registry

### Self-Hosted
- VPS with Docker
- Kubernetes cluster
- Local server

## 🔒 Security Features

- Input validation for video URLs
- Rate limiting ready (add middleware)
- CORS configuration
- Headless browser sandboxing
- No persistent video storage

## 🛠️ Development

### Project Structure
```
shot.in/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Multi-service setup
├── .env.example        # Environment template
├── cache/              # Local screenshot cache
└── README.md           # This file
```

### Adding Features
- Extend `main.py` for new endpoints
- Modify `capture_video_screenshot()` for platform-specific handling
- Update `process_screenshot()` for image processing features

## 📊 Performance

- **Cold start**: ~3-5 seconds (browser initialization)
- **Cached response**: ~10-50ms
- **Memory usage**: ~100-200MB per browser instance
- **Concurrent requests**: Scales with available memory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**shot.in** - Precise video screenshots, delivered instantly. 🎬✨
