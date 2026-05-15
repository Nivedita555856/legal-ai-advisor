from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
from loguru import logger
import tempfile
import os

from agents.orchestrator import LegalOrchestrator
from ingestion.ingest import DocumentIngester
from tools.supabase_client import SupabaseClient
from tools.lawyer_finder import LawyerFinder
from tools.draft_generator import DraftGenerator
from tools.vector_store import VectorStore
from llm.groq_client import GroqClient

router = APIRouter()

_orchestrator = None
_ingester = None
_supabase = None
_lawyer_finder = None
_vector_store = None
_llm = None


def get_orchestrator():
    global _orchestrator
    if not _orchestrator:
        _orchestrator = LegalOrchestrator()
    return _orchestrator

def get_ingester():
    global _ingester
    if not _ingester:
        _ingester = DocumentIngester()
    return _ingester

def get_supabase():
    global _supabase
    if not _supabase:
        _supabase = SupabaseClient()
    return _supabase

def get_lawyer_finder():
    global _lawyer_finder
    if not _lawyer_finder:
        _lawyer_finder = LawyerFinder()
    return _lawyer_finder

def get_vector_store():
    global _vector_store
    if not _vector_store:
        _vector_store = VectorStore()
    return _vector_store

def get_llm():
    global _llm
    if not _llm:
        _llm = GroqClient()
    return _llm


class QueryRequest(BaseModel):
    query: str
    jurisdiction: str = "India"

class DraftRequest(BaseModel):
    scenario: str
    doc_type: str = "notice"
    parties: str = "Party A and Party B"
    jurisdiction: str = "India"

class LawyerRequest(BaseModel):
    city: str = "Bangalore"
    practice_area: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "AI Legal Document Advisor", "version": "1.0.0"}


@router.post("/query")
async def query_documents(request: QueryRequest):
    try:
        result = await get_orchestrator().run(request.query, request.jurisdiction)
        # Build rich source list with type, label, and score
        chunks = result.get("retrieved_chunks", [])
        sources = [
            {
                "document": c.get("document", ""),
                "score": round(c.get("combined_score", c.get("score", 0)), 3),
                "source_type": c.get("source_type", "vector"),
                "source_label": c.get("source_label", c.get("document", "Document")),
            }
            for c in chunks[:6] if c.get("document") or c.get("source_label")
        ]

        return {
            "success": True,
            "query": request.query,
            "jurisdiction": request.jurisdiction,
            "answer": result.get("final_answer", ""),
            "risk_score": result.get("risk_score", {}),
            "contradictions": result.get("contradictions", []),
            "similar_cases": result.get("similar_cases", []),
            "lawyers": result.get("lawyers", []),
            "rag_strategy": result.get("rag_strategy", ""),
            "mcts_path": result.get("mcts_path", []),
            "mcts_top_action": result.get("mcts_top_action", ""),
            "draft": result.get("draft", ""),
            "needs_human_review": result.get("needs_human", False),
            "retrieved_chunks": sources,
        }
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_name: Optional[str] = Form(None),
):
    allowed = {".pdf", ".txt", ".md"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: {allowed}")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        name = doc_name or file.filename or "uploaded_document"
        result = await get_ingester().ingest_file(tmp_path, name)
        os.unlink(tmp_path)
        return {"success": True, "message": "Document ingested successfully", **result}
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents():
    try:
        docs = await get_supabase().get_documents()
        return {"success": True, "documents": docs, "count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/stats")
async def document_stats():
    try:
        stats = get_vector_store().get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_documents(request: SearchRequest):
    try:
        results = get_vector_store().search(request.query, top_k=request.top_k)
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lawyers")
async def find_lawyers(request: LawyerRequest):
    try:
        lawyers = await get_lawyer_finder().find(request.city, request.practice_area)
        return {"success": True, "lawyers": lawyers, "city": request.city}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/draft")
async def generate_draft(request: DraftRequest):
    try:
        dg = DraftGenerator(get_llm())
        draft = await dg.generate(
            scenario=request.scenario,
            doc_type=request.doc_type,
            parties=request.parties,
            jurisdiction=request.jurisdiction,
        )
        return {"success": True, "draft": draft, "doc_type": request.doc_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize")
async def summarize_text(request: QueryRequest):
    try:
        dg = DraftGenerator(get_llm())
        result = await dg.summarize_document(request.query)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyses")
async def list_analyses():
    try:
        analyses = await get_supabase().get_analyses()
        return {"success": True, "analyses": analyses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
