# 🏗️ Prompt2Figma Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FIGMA DESKTOP APP                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Prompt2Figma Plugin (TypeScript)              │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  UI (ui.html + ui.js)                                │  │ │
│  │  │  - Prompt input                                      │  │ │
│  │  │  - Device selection (mobile/desktop)                 │  │ │
│  │  │  - Generate/Edit buttons                             │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Plugin Backend (code.ts)                            │  │ │
│  │  │  - Wireframe rendering                               │  │ │
│  │  │  - Figma API integration                             │  │ │
│  │  │  - Content validation                                │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                         │
│                  https://your-app.railway.app                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  API Endpoints (app/api/v1/endpoints.py)                  │ │
│  │  - POST /api/v1/generate-wireframe                        │ │
│  │  - POST /api/v1/generate-code                             │ │
│  │  - POST /api/v1/design-sessions                           │ │
│  │  - GET  /health                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                 │                                │
│                                 ▼                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Orchestrator (app/core/services/orchestrator.py)         │ │
│  │  - Request validation                                      │ │
│  │  - Task coordination                                       │ │
│  │  - Response formatting                                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                    │                           │
                    │                           │
        ┌───────────┘                           └───────────┐
        │                                                   │
        ▼                                                   ▼
┌──────────────────────┐                    ┌──────────────────────┐
│   CELERY WORKER      │                    │    REDIS DATABASE    │
│                      │                    │                      │
│  Task Pipeline       │◄───────────────────│  - Message Broker    │
│  (app/tasks/)        │                    │  - Result Backend    │
│                      │                    │  - State Store       │
│  - Wireframe Gen     │                    │  - Session Cache     │
│  - Code Generation   │                    │                      │
│  - AST Validation    │                    │  redis://redis:6379  │
└──────────────────────┘                    └──────────────────────┘
        │
        │ API Call
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE GEMINI API                             │
│              https://generativelanguage.googleapis.com           │
│                                                                   │
│  - Natural language processing                                   │
│  - Wireframe JSON generation                                     │
│  - React code generation                                         │
│  - Context-aware editing                                         │
│                                                                   │
│  Free Tier: 60 req/min, 1500 req/day                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Wireframe Generation Flow

```
User Input (Prompt)
    │
    ▼
Plugin UI (ui.js)
    │
    │ POST /api/v1/generate-wireframe
    │ { prompt: "...", devicePreference: "mobile" }
    ▼
FastAPI Endpoint
    │
    ▼
Orchestrator
    │
    │ Enqueue Task
    ▼
Celery Worker
    │
    │ API Call
    ▼
Google Gemini API
    │
    │ Returns JSON
    ▼
Celery Worker
    │
    │ Validate & Store
    ▼
Redis (State Store)
    │
    │ Return Result
    ▼
FastAPI Response
    │
    │ JSON Wireframe
    ▼
Plugin Backend (code.ts)
    │
    │ Parse & Render
    ▼
Figma Canvas
    │
    ▼
User sees Wireframe ✨
```

### 2. Code Generation Flow

```
User clicks "Generate Code"
    │
    ▼
Plugin UI (ui.js)
    │
    │ POST /api/v1/generate-code
    │ { wireframeJson: {...} }
    ▼
FastAPI Endpoint
    │
    ▼
Celery Worker
    │
    │ Generate React Code
    ▼
AST Validation (Node.js)
    │
    │ Validate Syntax
    ▼
Celery Worker
    │
    │ Return Validated Code
    ▼
FastAPI Response
    │
    │ React Component Code
    ▼
Plugin UI
    │
    │ Display in Code Output
    ▼
User copies code 📋
```

---

## Component Details

### Frontend (Figma Plugin)

**Technology**: TypeScript, HTML, CSS
**Build Tool**: esbuild
**Size**: ~500 KB (built)

**Key Files**:
- `src/main/code.ts` - Plugin backend logic
- `src/ui/ui.html` - UI markup
- `src/ui/ui.js` - UI logic and API calls
- `manifest.json` - Plugin configuration

**Responsibilities**:
- User interface
- API communication
- Wireframe rendering on Figma canvas
- Device preference management
- Error handling

### Backend API (FastAPI)

**Technology**: Python 3.9+, FastAPI
**Port**: 8000
**Endpoints**: 5+ REST endpoints

**Key Files**:
- `app/main.py` - FastAPI application
- `app/api/v1/endpoints.py` - API routes
- `app/core/services/orchestrator.py` - Business logic
- `app/core/config.py` - Configuration

**Responsibilities**:
- Request validation
- Task orchestration
- Response formatting
- CORS handling
- Health checks

### Celery Worker

**Technology**: Python 3.9+, Celery
**Concurrency**: 1 worker (free tier)

**Key Files**:
- `app/tasks/celery_app.py` - Celery configuration
- `app/tasks/pipeline.py` - Task pipeline
- `app/tasks/ast_validation.js` - Code validation

**Responsibilities**:
- Async task processing
- AI API calls
- Code generation
- AST validation
- Result caching

### Redis Database

**Technology**: Redis 5.0+
**Databases**: 3 (broker, results, state)

**Usage**:
- Database 0: Celery message broker
- Database 0: Celery result backend
- Database 1: Application state store

**Responsibilities**:
- Task queue management
- Result storage
- Session state
- Caching

### Google Gemini API

**Model**: gemini-pro
**Rate Limits**: 60/min, 1500/day (free tier)

**Usage**:
- Prompt analysis
- Wireframe JSON generation
- Code generation
- Context understanding

---

## Deployment Architecture

### Railway.app Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                    RAILWAY PROJECT                           │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Web Service    │  │  Worker Service │  │   Redis     │ │
│  │  (FastAPI)      │  │  (Celery)       │  │  Database   │ │
│  │                 │  │                 │  │             │ │
│  │  Port: 8000     │  │  No port        │  │  Port: 6379 │ │
│  │  Public URL     │  │  Internal only  │  │  Internal   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│         │                      │                    │        │
│         └──────────────────────┴────────────────────┘        │
│                    Internal Network                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
                    ┌──────────────────┐
                    │  Figma Plugin    │
                    │  (User's Device) │
                    └──────────────────┘
```

### Render.com Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                    RENDER ACCOUNT                            │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Web Service    │  │  Background     │  │   Redis     │ │
│  │  (FastAPI)      │  │  Worker         │  │  Instance   │ │
│  │                 │  │  (Celery)       │  │             │ │
│  │  Auto-deploy    │  │  Auto-deploy    │  │  Managed    │ │
│  │  from GitHub    │  │  from GitHub    │  │  Service    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│         │                      │                    │        │
│         └──────────────────────┴────────────────────┘        │
│                    Private Network                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Authentication & Authorization

```
Plugin Request
    │
    ▼
HTTPS (TLS 1.2+)
    │
    ▼
CORS Validation
    │
    ▼
Rate Limiting
    │
    ▼
Input Sanitization
    │
    ▼
API Processing
```

### Security Layers

1. **Transport Security**
   - HTTPS only
   - TLS 1.2+
   - Certificate validation

2. **Request Validation**
   - CORS headers
   - Content-Type validation
   - Request size limits

3. **Rate Limiting**
   - Per-minute limits
   - Per-hour limits
   - Per-day limits

4. **Input Sanitization**
   - XSS prevention
   - SQL injection prevention
   - Command injection prevention

5. **API Key Security**
   - Environment variables only
   - Never in code
   - Rotation support

---

## Scaling Architecture

### Current (Free Tier)

```
1 Web Service (FastAPI)
1 Celery Worker
1 Redis Instance
~100-500 requests/day
```

### Small Scale ($5-10/month)

```
1 Web Service (always-on)
2 Celery Workers
1 Redis Instance
~1000-5000 requests/day
```

### Medium Scale ($20-50/month)

```
2-3 Web Services (load balanced)
5-10 Celery Workers
1 Redis Instance (larger)
~10,000-50,000 requests/day
```

### Large Scale ($100+/month)

```
5+ Web Services (auto-scaling)
20+ Celery Workers (auto-scaling)
Redis Cluster
CDN for static assets
~100,000+ requests/day
```

---

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MONITORING STACK                          │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  UptimeRobot    │  │  Sentry         │  │ Better Stack│ │
│  │  (Uptime)       │  │  (Errors)       │  │ (Logs)      │ │
│  │                 │  │                 │  │             │ │
│  │  - Health check │  │  - Error track  │  │  - Log agg  │ │
│  │  - Alerts       │  │  - Performance  │  │  - Search   │ │
│  │  - Status page  │  │  - Traces       │  │  - Alerts   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│         │                      │                    │        │
│         └──────────────────────┴────────────────────┘        │
│                    Monitoring Data                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Email/Slack     │
                    │  Notifications   │
                    └──────────────────┘
```

---

## Technology Stack Summary

### Frontend
- **Language**: TypeScript
- **UI**: HTML5, CSS3, JavaScript
- **Build**: esbuild
- **Testing**: Vitest
- **Platform**: Figma Plugin API

### Backend
- **Language**: Python 3.9+
- **Framework**: FastAPI
- **Task Queue**: Celery
- **Validation**: Pydantic
- **ASGI Server**: Uvicorn

### Database
- **Primary**: Redis 5.0+
- **Purpose**: Queue, Cache, State

### AI/ML
- **Provider**: Google Gemini
- **Model**: gemini-pro
- **API**: REST

### DevOps
- **Hosting**: Railway/Render/Fly.io
- **CI/CD**: GitHub Actions (optional)
- **Monitoring**: UptimeRobot, Sentry
- **Logs**: Better Stack

### Development
- **Version Control**: Git
- **Package Managers**: npm, pip
- **Code Quality**: Black, isort, mypy
- **Testing**: pytest, Vitest

---

## Performance Characteristics

### Response Times (Target)

- Health Check: < 100ms
- Wireframe Generation: < 3s
- Code Generation: < 5s
- Edit Application: < 2s
- History Retrieval: < 500ms

### Throughput (Free Tier)

- Concurrent Users: 10-50
- Requests/Day: 100-500
- Requests/Minute: 10-20
- Peak Load: 5 req/sec

### Resource Usage

- Memory: 512MB - 1GB
- CPU: 0.5 - 1 vCPU
- Storage: < 1GB
- Bandwidth: 1-5GB/month

---

## Future Architecture Considerations

### Potential Improvements

1. **Caching Layer**
   - Cache common prompts
   - Reduce AI API calls
   - Faster response times

2. **CDN Integration**
   - Serve static assets
   - Reduce latency
   - Global distribution

3. **Database Addition**
   - PostgreSQL for persistence
   - User accounts
   - Design history

4. **Microservices**
   - Separate services
   - Independent scaling
   - Better isolation

5. **Kubernetes**
   - Container orchestration
   - Auto-scaling
   - High availability

---

## Conclusion

This architecture provides:
- ✅ Scalable foundation
- ✅ Cost-effective start (free tier)
- ✅ Easy deployment
- ✅ Production-ready
- ✅ Monitoring capabilities
- ✅ Security best practices

**Start simple, scale as needed!** 🚀
