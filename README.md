# Prompt2Figma

An AI-powered Figma plugin that transforms natural language prompts into interactive UI designs with iterative editing capabilities.

## Overview

Prompt2Figma is a full-stack application that bridges the gap between design ideation and implementation. It allows designers and developers to create Figma wireframes using natural language prompts, iteratively refine them through conversational edits, and generate production-ready React code.

### Key Features

- **Natural Language Design**: Create UI wireframes from simple text prompts
- **Iterative Editing**: Refine designs through conversational edits with full context awareness
- **Version History**: Track all design iterations with complete version control
- **Code Generation**: Export designs as validated React components
- **Session Management**: Maintain design state across multiple editing sessions
- **Security First**: Built-in rate limiting, input sanitization, and attack prevention

## Architecture

The project consists of two main components:

### Backend (FastAPI + Celery)
- RESTful API for design session management
- Asynchronous task processing with Celery
- Redis-based state management and caching
- AI-powered wireframe generation using Ollama/Google Gemini
- React code generation with AST validation

### Frontend (Figma Plugin)
- TypeScript-based Figma plugin
- Real-time design rendering on Figma canvas
- Session-based workflow with version history
- Intuitive UI for prompt input and design editing

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Task Queue**: Celery + Redis
- **AI/ML**: Google Generative AI (Gemini), Ollama support
- **State Management**: Redis
- **Language**: Python 3.8+
- **Code Validation**: Node.js + Babel Parser

### Frontend
- **Platform**: Figma Plugin API
- **Language**: TypeScript
- **Build Tool**: esbuild
- **Testing**: Vitest

## Project Structure

```
prompt2Figma/
├── prompt2Figma-Backend/          # Backend API server
│   ├── app/
│   │   ├── api/                   # API endpoints
│   │   │   └── v1/
│   │   │       ├── endpoints.py   # Route handlers
│   │   │       └── schemas.py     # Pydantic models
│   │   ├── core/                  # Core business logic
│   │   │   ├── config.py          # Configuration
│   │   │   └── services/          # Service layer
│   │   │       └── orchestrator.py
│   │   ├── tasks/                 # Celery tasks
│   │   │   ├── celery_app.py      # Celery configuration
│   │   │   ├── pipeline.py        # Task pipeline
│   │   │   └── ast_validation.js  # Code validation
│   │   └── main.py                # FastAPI app entry
│   ├── tests/                     # Backend tests
│   ├── requirements.txt           # Python dependencies
│   └── environment.yml            # Conda environment
│
└── prompt2Figma-Frontend (Plugin)/ # Figma plugin
    ├── src/
    │   ├── main/                  # Plugin backend code
    │   │   ├── code.ts            # Main plugin logic
    │   │   └── content-validation.ts
    │   └── ui/                    # Plugin UI
    │       ├── ui.html            # UI markup
    │       ├── ui.js              # UI logic
    │       └── styles.css         # Styling
    ├── tests/                     # Frontend tests
    ├── dist/                      # Build output
    ├── manifest.json              # Plugin manifest
    └── package.json               # Node dependencies
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- Redis server
- Figma Desktop App
- Google Gemini API key (or Ollama installation)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd prompt2Figma-Backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
npm install  # For AST validation
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start Redis server:
```bash
redis-server
```

6. Start Celery worker:
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

7. Start the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to the plugin directory:
```bash
cd "prompt2Figma-Frontend (Plugin)"
```

2. Install dependencies:
```bash
npm install
```

3. Build the plugin:
```bash
npm run build
```

4. Load the plugin in Figma:
   - Open Figma Desktop App
   - Go to Plugins → Development → Import plugin from manifest
   - Select the `manifest.json` file from the plugin directory

## Usage

### Creating a Design Session

1. Open the Prompt2Figma plugin in Figma
2. Enter a natural language prompt (e.g., "Create a login form with email and password")
3. Click "Generate" to create the initial wireframe
4. The design appears on your Figma canvas

### Iterative Editing

1. Enter an edit prompt (e.g., "Add a forgot password link")
2. Click "Apply Edit" to refine the design
3. The plugin maintains full context of previous edits
4. View version history to see all iterations

### Generating Code

1. Once satisfied with the design, click "Generate Code"
2. Receive validated React component code
3. Copy and use in your project

## API Endpoints

### Design Sessions
- `POST /api/v1/design-sessions` - Create new session
- `GET /api/v1/design-sessions/{id}` - Get session details
- `POST /api/v1/design-sessions/{id}/edit` - Apply iterative edit
- `GET /api/v1/design-sessions/{id}/history` - Get version history
- `POST /api/v1/design-sessions/{id}/generate-code` - Generate React code

### Code Generation
- `POST /api/v1/generate-wireframe` - Generate wireframe from prompt
- `POST /api/v1/generate-code` - Generate React code from wireframe

For detailed API documentation, visit `http://localhost:8000/docs` when the server is running.

## Testing

### Backend Tests
```bash
cd prompt2Figma-Backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd "prompt2Figma-Frontend (Plugin)"
npm test
```

### Coverage Reports
```bash
# Backend
pytest --cov=app tests/

# Frontend
npm run test:coverage
```

## Security Features

- **Rate Limiting**: Per-minute, per-hour, and per-day limits
- **Input Sanitization**: Protection against XSS, SQL injection, and command injection
- **Session Security**: Cryptographic session IDs with validation
- **Attack Prevention**: Circuit breaker pattern for resilience
- **Audit Logging**: Comprehensive security event tracking

## Performance

- Session creation: < 3 seconds
- Edit application: < 2 seconds
- History retrieval: < 500ms
- Code generation: < 5 seconds
- Concurrent sessions: 1000+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request



## Support

For issues, questions, or contributions, please open an issue on the project repository.

## Acknowledgments

- Built with FastAPI, Celery, and the Figma Plugin API
- AI-powered by Google Gemini and Ollama
- Inspired by the need for faster design-to-code workflows
