# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as v1_router

app = FastAPI(
    title="Prompt2Figma API",
    description="API for generating UI wireframes and code with iterative design capabilities",
    version="1.0.0"
)

# ⚠️ For development, wide-open CORS is simplest. Tighten later if needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or restrict to your origin(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Prompt2Figma API",
        "version": "1.0.0",
        "features": ["wireframe_generation", "code_generation", "iterative_design"]
    }
