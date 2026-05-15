"""
Legal Advisor MCP Server — Claude Integration
Exposes legal tools via stdio transport for Claude Desktop and Claude Code.
Run: python mcp_legal_server.py
"""
import sys
import os

# ── Fix import collision: remove backend/ from path so 'mcp' finds the installed package,
#    then re-add it after mcp imports are done for the legal advisor modules ──────────────
_backend_dir = os.path.dirname(os.path.abspath(__file__))

# Remove backend dir temporarily so Python finds the pip-installed mcp package
_saved_path = [p for p in sys.path if p != _backend_dir and p != '']
sys.path = _saved_path

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Now restore the backend path for legal advisor imports
sys.path.insert(0, _backend_dir)
from dotenv import load_dotenv
load_dotenv(os.path.join(_backend_dir, "..", ".env"))
from loguru import logger

server = Server("legal-advisor")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_legal_documents",
            description="Search Indian legal documents using semantic vector search. Returns relevant clauses with confidence scores from Pinecone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Legal question or scenario to search"},
                    "top_k": {"type": "integer", "description": "Number of results (default 5)", "default": 5}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="analyze_legal_query",
            description="Full AI legal analysis using Ensemble RAG + MCTS + Groq LLaMA. Returns structured answer with section citations, case law, actionable steps, risk score, and source confidence scores.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Legal question or scenario"},
                    "jurisdiction": {"type": "string", "description": "India, Maharashtra, Karnataka, Delhi, Tamil Nadu", "default": "India"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="generate_legal_draft",
            description="Generate professional Indian legal documents: legal notice, demand letter, consumer complaint, NDA, employment termination, domestic violence application, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "scenario": {"type": "string", "description": "Describe the legal situation and parties"},
                    "doc_type": {"type": "string", "description": "notice, nda, employment, demand_letter, lease, service, termination, partnership"},
                    "parties": {"type": "string", "description": "Parties involved e.g. ABC Ltd (Employer) and John Doe (Employee)"},
                    "jurisdiction": {"type": "string", "default": "India"}
                },
                "required": ["scenario"]
            }
        ),
        Tool(
            name="find_lawyers",
            description="Find Indian lawyers by city and practice area. Returns name, firm, experience, rating, contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Bangalore, Mumbai, Delhi, Chennai, Hyderabad"},
                    "practice_area": {"type": "string", "description": "Contract Law, Employment Law, Property Law, Data Privacy Law, Consumer Law, IP"}
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="web_search_legal",
            description="Live web search for Indian case law (indiankanoon.org), government advisories (pib.gov.in), and legal news.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Legal topic or case to search"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="check_index_stats",
            description="Check Pinecone vector database — total documents indexed and embedding dimensions.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "search_legal_documents":
            return await _search(arguments)
        elif name == "analyze_legal_query":
            return await _analyze(arguments)
        elif name == "generate_legal_draft":
            return await _draft(arguments)
        elif name == "find_lawyers":
            return await _lawyers(arguments)
        elif name == "web_search_legal":
            return await _web(arguments)
        elif name == "check_index_stats":
            return await _stats()
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error in {name}: {e}")]


async def _search(args):
    from tools.vector_store import VectorStore
    vs = VectorStore()
    results = vs.search(args["query"], top_k=args.get("top_k", 5))
    if not results:
        return [TextContent(type="text", text="No relevant documents found.")]
    lines = [f"Found {len(results)} results for: {args['query']}\n"]
    for i, r in enumerate(results, 1):
        pct = round(r.get("score", 0) * 100, 1)
        doc = r.get("document", "?").replace(".md", "")
        text = r.get("text", "")[:250]
        lines.append(f"{i}. [{doc}] {pct}% confidence\n{text}\n")
    return [TextContent(type="text", text="\n".join(lines))]


async def _analyze(args):
    import httpx
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post("http://localhost:8000/api/query",
                json={"query": args["query"], "jurisdiction": args.get("jurisdiction", "India")})
            d = r.json()
            ans = d.get("answer", "No answer.")
            risk = d.get("risk_score", {})
            sources = d.get("retrieved_chunks", [])
            mcts = d.get("mcts_top_action", "")
            out = f"LEGAL ANALYSIS\n{'='*50}\n\n{ans}\n"
            if risk.get("level"):
                out += f"\nRisk: {risk['level']} ({risk.get('score',0)}/100)"
            if mcts:
                out += f"\nMCTS Strategy: {mcts}"
            if sources:
                out += "\n\nSources:"
                for s in sources[:4]:
                    pct = round(s.get("score", 0) * 100, 1)
                    out += f"\n  - {s.get('document','').replace('.md','')} ({pct}%)"
            return [TextContent(type="text", text=out)]
    except Exception as e:
        return [TextContent(type="text", text=f"Backend API error (is uvicorn running on port 8000?): {e}")]


async def _draft(args):
    import httpx
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post("http://localhost:8000/api/draft", json={
                "scenario": args["scenario"],
                "doc_type": args.get("doc_type", "notice"),
                "parties": args.get("parties", "Party A and Party B"),
                "jurisdiction": args.get("jurisdiction", "India")
            })
            draft = r.json().get("draft", "Draft generation failed.")
            return [TextContent(type="text", text=f"LEGAL DRAFT\n{'='*50}\n\n{draft}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Backend API error: {e}")]


async def _lawyers(args):
    import httpx
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post("http://localhost:8000/api/lawyers",
                json={"city": args["city"], "practice_area": args.get("practice_area")})
            lawyers = r.json().get("lawyers", [])
            if not lawyers:
                return [TextContent(type="text", text="No lawyers found.")]
            lines = [f"Lawyers in {args['city']}:\n"]
            for l in lawyers:
                lines.append(
                    f"  {l['name']} — {l['firm']}\n"
                    f"  Areas: {', '.join(l.get('practice_areas',[])[:2])}\n"
                    f"  Experience: {l.get('experience','?')}yr | Rating: {l.get('rating','?')}/5\n"
                    f"  Contact: {l.get('contact','N/A')}\n"
                )
            return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]


async def _web(args):
    from tools.web_search import WebSearch
    ws = WebSearch()
    result = await ws.search(args["query"])
    return [TextContent(type="text", text=f"Web Results:\n\n{result}")]


async def _stats():
    from tools.vector_store import VectorStore
    vs = VectorStore()
    s = vs.get_stats()
    return [TextContent(type="text", text=
        f"Pinecone Index: legal-advisor\n"
        f"Total vectors: {s.get('total_vector_count', 0)}\n"
        f"Dimension: {s.get('dimension', 384)}\n"
        f"Embedding model: all-MiniLM-L6-v2 (local, free)")]


async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
