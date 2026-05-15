from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (one level up from backend/)
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

from api.routes import router
from config import settings

app = FastAPI(
    title="AI Legal Document Advisor",
    description="Intelligent legal document analysis using multi-agent RAG orchestration",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "AI Legal Document Advisor",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "api": "/api",
            "health": "/api/health"
        }
    }

@app.on_event("startup")
async def startup_event():
    logger.info("AI Legal Document Advisor starting up...")
    logger.info(f"Groq model: {settings.groq_model}")
    logger.info(f"Pinecone index: {settings.pinecone_index_name}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
