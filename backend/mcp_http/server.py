from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from loguru import logger
import uvicorn

from config import settings

mcp_app = FastAPI(title="Legal Advisor MCP Server", version="1.0.0")
mcp_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

TOOLS = {
    "search_legal_documents": {
        "description": "Search legal documents using vector similarity",
        "parameters": {"query": "string", "top_k": "int (optional)"},
    },
    "find_lawyers": {
        "description": "Find lawyers by city and practice area",
        "parameters": {"city": "string", "practice_area": "string (optional)"},
    },
    "generate_draft": {
        "description": "Generate a legal document draft",
        "parameters": {"scenario": "string", "doc_type": "string"},
    },
    "web_search_legal": {
        "description": "Search the web for legal information",
        "parameters": {"query": "string"},
    },
}


class MCPToolRequest(BaseModel):
    tool: str
    parameters: Dict[str, Any] = {}

class MCPToolResponse(BaseModel):
    result: Any
    tool: str
    success: bool
    error: Optional[str] = None


@mcp_app.get("/tools")
async def list_tools():
    return {"tools": TOOLS}


@mcp_app.post("/invoke", response_model=MCPToolResponse)
async def invoke_tool(request: MCPToolRequest):
    from tools.vector_store import VectorStore
    from tools.lawyer_finder import LawyerFinder
    from tools.web_search import WebSearch
    from llm.groq_client import GroqClient
    from tools.draft_generator import DraftGenerator

    tool = request.tool
    params = request.parameters
    try:
        if tool == "search_legal_documents":
            results = VectorStore().search(params["query"], top_k=params.get("top_k", 10))
            return MCPToolResponse(tool=tool, result=results, success=True)
        elif tool == "find_lawyers":
            lawyers = await LawyerFinder().find(
                area=params.get("city", "Bangalore"),
                practice_area=params.get("practice_area"),
            )
            return MCPToolResponse(tool=tool, result=lawyers, success=True)
        elif tool == "web_search_legal":
            result = await WebSearch().search(params["query"])
            return MCPToolResponse(tool=tool, result=result, success=True)
        elif tool == "generate_draft":
            draft = await DraftGenerator(GroqClient()).generate(
                scenario=params["scenario"],
                doc_type=params.get("doc_type", "notice"),
                parties=params.get("parties", "Party A and Party B"),
            )
            return MCPToolResponse(tool=tool, result=draft, success=True)
        else:
            return MCPToolResponse(tool=tool, result=None, success=False, error=f"Unknown tool: {tool}")
    except Exception as e:
        logger.error(f"MCP tool {tool} error: {e}")
        return MCPToolResponse(tool=tool, result=None, success=False, error=str(e))


@mcp_app.get("/health")
async def health():
    return {"status": "ok", "service": "Legal MCP Server"}


if __name__ == "__main__":
    uvicorn.run(mcp_app, host="0.0.0.0", port=settings.mcp_port)
