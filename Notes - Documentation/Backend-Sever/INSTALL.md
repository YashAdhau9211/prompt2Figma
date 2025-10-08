# Installation Guide - Prompt2Figma

This guide will help you set up the Prompt2Figma backend API project.

## Prerequisites

### Required Software
- **Python 3.8+** (recommended: Python 3.11 or 3.13)
- **Node.js 16+** (for AST validation)
- **Redis Server** (for Celery task queue)
- **Git** (for cloning and version control)

### Optional but Recommended
- **uv** (fast Python package manager) - [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
- **Docker** (for containerized Redis)

## Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
# Clone the repository
git clone <your-repo-url>
cd prompt2figma_backend

# Run the setup script
python setup.py
```

### Option 2: Manual Setup

#### 1. Install Python Dependencies
```bash
# Install main backend dependencies
pip install -r requirements.txt


```

#### 2. Install Node.js Dependencies
```bash
npm install
```

#### 3. Set Up Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required: GEMINI_API_KEY, CELERY_BROKER_URL, CELERY_RESULT_BACKEND
```

## Configuration

### Environment Variables (.env)
```bash
# AI API Configuration
GEMINI_API_KEY="your_gemini_api_key_here"

# Celery Configuration
CELERY_BROKER_URL="amqp://guest:guest@localhost:5672//"
CELERY_RESULT_BACKEND="redis://localhost:6379/0"


```

### Redis Setup

#### Option 1: Local Redis
```bash
# Install Redis (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

# Install Redis (macOS with Homebrew)
brew install redis

# Install Redis (Windows)
# Download from: https://redis.io/download
```

#### Option 2: Docker Redis
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

## Running the Application

### 1. Start Redis Server
```bash
# Local installation
redis-server

# Or with Docker
docker start redis
```

### 2. Start Celery Worker
```bash
# In a new terminal
celery -A app.tasks.celery_app worker --loglevel=info
```

### 3. Start the Backend API
```bash
# In another terminal
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test the Installation
```bash
# Test the backend API
curl http://localhost:8000/api/v1/generate-wireframe \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a simple button"}'


```



## Development Setup

### Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### Code Quality Tools
```bash
# Format code
black .
isort .

# Type checking
mypy app/

# Run tests
pytest
```

## Troubleshooting

### Common Issues

#### 1. Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running, start Redis
redis-server
```

#### 2. Celery Worker Not Starting
```bash
# Check Celery configuration
celery -A app.tasks.celery_app inspect active

# Clear any stuck tasks
celery -A app.tasks.celery_app purge
```



#### 4. Node.js AST Validation Failing
```bash
# Test Node.js script directly
echo "const test = 'hello';" | node app/tasks/ast_validation.js

# Reinstall Node dependencies if needed
npm install
```

### Getting Help

1. Check the logs in your terminal windows
2. Verify all services are running (Redis, Celery, Backend)
3. Ensure environment variables are set correctly
4. Test each component individually

## Production Deployment

For production deployment, consider:

1. **Use a process manager** (PM2, systemd, or Docker)
2. **Set up proper logging** (structured logging with external services)
3. **Use a production Redis instance** (Redis Cloud, AWS ElastiCache)
4. **Configure proper CORS** settings in FastAPI
5. **Set up monitoring** (health checks, metrics)
6. **Use HTTPS** with proper SSL certificates

## Next Steps

After installation:

1. **Test the API endpoints** with your favorite HTTP client

3. **Explore the Figma plugin integration** (if available)
4. **Customize the AI prompts** for your specific use cases
5. **Set up monitoring and logging** for production use