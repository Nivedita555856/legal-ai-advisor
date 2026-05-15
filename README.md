# AI Legal Document Advisor

A production-ready AI system for intelligent legal document analysis using multi-agent orchestration, 5 RAG strategies, MCTS planning, and a knowledge graph.

## Architecture

```
[React Frontend] <──> [FastAPI Backend] <──> [LangGraph Orchestrator]
                                                      │
              [AutoGen Agents] <──> [Crew AI Agents] <──> [MCTS Planner]
                                                      │
              [Vector RAG] [HyDE RAG] [Self RAG] [Corrective RAG] [Parent-Child RAG]
                                                      │
              [Supabase] [Pinecone] [Neo4j] [Tavily Web Search]
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Tailwind CSS |
| Backend | FastAPI + Uvicorn |
| LLM | Groq Llama 3 70B |
| Embeddings | OpenAI text-embedding-3-small (1536d) |
| Vector DB | Pinecone |
| Graph DB | Neo4j Aura |
| Database | Supabase (PostgreSQL) |
| Web Search | Tavily API |
| Agents | AutoGen + Crew AI + LangGraph |
| Planning | MCTS (Monte Carlo Tree Search) |
| Deployment | Render |

## Setup

### 1. Clone and configure environment

```bash
cp .env.example .env
# Fill in all API keys in .env
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Ingest documents

```bash
# Via API
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/contract.pdf"

# Or via UI — Documents page → drag & drop
```

## Environment Variables

See `.env` file for all required variables:
- `SUPABASE_URL` + `SUPABASE_SERVICE_KEY`
- `PINECONE_API_KEY` + `PINECONE_ENVIRONMENT`
- `GROQ_API_KEY`
- `OPENAI_API_KEY` (for embeddings)
- `NEO4J_URI` + `NEO4J_USER` + `NEO4J_PASSWORD`
- `TAVILY_API_KEY`

## Supabase Setup

Run this SQL in your Supabase SQL editor once:

```sql
CREATE TABLE IF NOT EXISTS documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    file_type TEXT,
    content TEXT,
    chunk_count INT DEFAULT 0,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    query TEXT,
    answer TEXT,
    risk_level TEXT,
    risk_score INT,
    rag_strategy TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Deploy to Render

1. Push to GitHub
2. Create a new **Web Service** on Render pointing to `backend/`
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables in Render dashboard
6. For frontend: create a **Static Site** pointing to `frontend/` with build command `npm install && npm run build` and publish dir `dist`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/query` | Full multi-agent query |
| POST | `/api/upload` | Upload & ingest document |
| GET | `/api/documents` | List all documents |
| POST | `/api/search` | Direct vector search |
| POST | `/api/lawyers` | Find lawyers |
| POST | `/api/draft` | Generate legal draft |
| POST | `/api/summarize` | Summarize document text |

## RAG Strategies

1. **Vector RAG** — Standard cosine similarity search
2. **HyDE RAG** — Hypothetical Document Embeddings (generates synthetic answer → embeds → retrieves)
3. **Self RAG** — Reflects on each retrieved chunk, filters by relevance confidence
4. **Corrective RAG** — Falls back to Tavily web search if vector confidence < 0.6
5. **Parent-Child RAG** — Retrieves small child chunks, returns broader parent context

## Disclaimer

This system is for informational purposes only and does not constitute legal advice. Always consult a qualified lawyer for specific legal guidance.
