from typing import TypedDict, List, Dict, Optional
from loguru import logger

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("langgraph not installed; using sequential fallback")

from llm.groq_client import GroqClient
from rag.router import RAGRouter
from agents.autogen_agents import AutoGenAgents
from agents.crew_agents import CrewAgents
from agents.mcts_planner import MCTSPlanner
from tools.human_loop import HumanLoop
from tools.lawyer_finder import LawyerFinder
from tools.draft_generator import DraftGenerator
from tools.vector_store import VectorStore
from tools.web_search import WebSearch
from tools.knowledge_graph import KnowledgeGraph
from tools.guardrails import Guardrails


class OrchestratorState(TypedDict, total=False):
    query: str
    jurisdiction: str
    documents: List[Dict]
    retrieved_chunks: List[Dict]
    rag_strategy: str
    mcts_path: List[Dict]
    autogen_analysis: Dict
    crew_analysis: Dict
    final_answer: str
    citations: List[Dict]
    risk_score: Dict
    contradictions: List[Dict]
    similar_cases: List[Dict]
    lawyers: List[Dict]
    needs_human: bool
    draft: str
    error: Optional[str]


class LegalOrchestrator:
    def __init__(self):
        self.llm = GroqClient()
        self.vector_store = VectorStore()
        self.web_search = WebSearch()
        self.kg = KnowledgeGraph()
        self.rag_router = RAGRouter(self.vector_store, self.llm, self.web_search, self.kg)
        self.autogen = AutoGenAgents(self.llm)
        self.crew = CrewAgents(self.llm)
        self.mcts = MCTSPlanner(self.llm)
        self.human_loop = HumanLoop()
        self.lawyer_finder = LawyerFinder()
        self.draft_generator = DraftGenerator(self.llm)
        self.guardrails = Guardrails()
        self.graph = self._build_graph() if LANGGRAPH_AVAILABLE else None

    def _build_graph(self):
        wf = StateGraph(OrchestratorState)
        wf.add_node("retrieve_documents", self.retrieve_documents)
        wf.add_node("mcts_plan", self.mcts_planning)
        wf.add_node("autogen_analyze", self.autogen_analysis)
        wf.add_node("crew_analyze", self.crew_analysis)
        wf.add_node("find_contradictions", self.find_contradictions)
        wf.add_node("assess_risks", self.assess_risks)
        wf.add_node("suggest_lawyers", self.suggest_lawyers)
        wf.add_node("generate_draft", self.generate_draft)
        wf.add_node("human_check", self.human_validation)
        wf.add_node("synthesize", self.synthesize_final)
        wf.set_entry_point("retrieve_documents")
        wf.add_edge("retrieve_documents", "mcts_plan")
        wf.add_edge("mcts_plan", "autogen_analyze")
        wf.add_edge("autogen_analyze", "crew_analyze")
        wf.add_edge("crew_analyze", "find_contradictions")
        wf.add_edge("find_contradictions", "assess_risks")
        wf.add_edge("assess_risks", "suggest_lawyers")
        wf.add_conditional_edges(
            "suggest_lawyers",
            self._route_after_lawyers,
            {"draft": "generate_draft", "human": "human_check", "synthesize": "synthesize"},
        )
        wf.add_edge("generate_draft", "human_check")
        wf.add_edge("human_check", "synthesize")
        wf.add_edge("synthesize", END)
        return wf.compile()

    async def retrieve_documents(self, state):
        logger.info("Retrieving documents...")
        _, result = await self.rag_router.route(state["query"])
        state["retrieved_chunks"] = result.chunks
        state["rag_strategy"] = result.strategy
        return state

    async def mcts_planning(self, state):
        logger.info("MCTS planning...")
        path = await self.mcts.search(state["query"], state.get("retrieved_chunks", []))
        state["mcts_path"] = path
        # Store top action so downstream steps can adapt depth
        if path:
            top_action = path[0].get("action", "")
            state["mcts_top_action"] = top_action
            logger.info(f"MCTS top action: {top_action}")
        return state

    async def autogen_analysis(self, state):
        """MCTS-guided: if top action is summarize_clauses or extract_obligations, do deeper analysis."""
        top = state.get("mcts_top_action", "")
        deep = top in ("summarize_clauses", "extract_obligations", "generate_recommendations")
        logger.info(f"AutoGen analysis (deep={deep}, mcts={top})...")
        state["autogen_analysis"] = await self.autogen.analyze(
            state["query"],
            state.get("retrieved_chunks", []),
            deep=deep
        )
        return state

    async def crew_analysis(self, state):
        """MCTS-guided: if top action is check_compliance or search_precedents, add those to prompt."""
        top = state.get("mcts_top_action", "")
        focus = top if top in ("check_compliance", "search_precedents", "find_contradictions") else None
        logger.info(f"Crew analysis (mcts_focus={focus})...")
        state["crew_analysis"] = await self.crew.analyze(
            state["query"],
            state.get("retrieved_chunks", []),
            state.get("jurisdiction", "India"),
            mcts_focus=focus,
        )
        return state

    async def find_contradictions(self, state):
        """MCTS-guided: run contradiction check only when MCTS recommends it or query suggests it."""
        top = state.get("mcts_top_action", "")
        if top == "find_contradictions" or any(
            w in state["query"].lower() for w in ["contradict", "conflict", "inconsistent", "differ"]
        ):
            logger.info("Detecting contradictions (MCTS-triggered)...")
            state["contradictions"] = await self.llm.detect_contradictions_batch(
                state.get("retrieved_chunks", [])
            )
        else:
            state["contradictions"] = []
        return state

    async def assess_risks(self, state):
        """MCTS-guided: deeper risk assessment when MCTS selects assess_risks or request_human_review."""
        top = state.get("mcts_top_action", "")
        logger.info(f"Assessing risks (mcts={top})...")
        state["risk_score"] = await self.llm.assess_risks(
            state["query"], state.get("retrieved_chunks", [])
        )
        # MCTS: if it recommends human review, force the flag regardless of risk level
        if top == "request_human_review":
            state["risk_score"]["level"] = "HIGH"
            state["risk_score"]["recommendation"] = "MCTS planner recommends human legal review for this query."
        return state

    async def suggest_lawyers(self, state):
        logger.info("Suggesting lawyers...")
        state["lawyers"] = await self.lawyer_finder.find(
            area=state.get("jurisdiction", "Bangalore"),
            practice_area=self._detect_practice_area(state["query"]),
        )
        return state

    async def generate_draft(self, state):
        logger.info("Generating draft...")
        state["draft"] = await self.draft_generator.generate(
            scenario=state["query"],
            documents=state.get("retrieved_chunks", []),
            jurisdiction=state.get("jurisdiction", "India"),
        )
        return state

    async def human_validation(self, state):
        if state.get("risk_score", {}).get("level") in ["HIGH", "CRITICAL"]:
            state["needs_human"] = True
            await self.human_loop.request_validation(state)
        return state

    def _is_scenario_based(self, query: str) -> bool:
        """Detect if query describes a real situation vs a general legal question."""
        scenario_keywords = [
            "my ", "i ", "we ", "our ", "employer", "employee", "company did",
            "they refused", "was fired", "terminated", "not paid", "breach",
            "dispute", "violated", "cheated", "sued", "notice served",
            "what should i", "what can i", "can i sue", "am i entitled",
            "did not", "didn't", "refused to", "failed to"
        ]
        q = query.lower()
        return any(kw in q for kw in scenario_keywords)

    async def synthesize_final(self, state):
        logger.info("Synthesizing final answer...")
        summary = state.get("autogen_analysis", {}).get("summary", "N/A")
        risk = state.get("risk_score", {})
        is_scenario = self._is_scenario_based(state["query"])

        if is_scenario:
            risk_section = f"\nRisk Level: {risk.get('level', 'MEDIUM')} ({risk.get('score', 50)}/100)\n"
        else:
            risk_section = ""

        prompt = f"""You are an expert Indian legal awareness advisor. Answer in plain English.
Do not use asterisks, markdown, or emojis. Write in clear numbered paragraphs.

Query: {state["query"]}

Relevant legal content from documents:
{summary[:700]}
{risk_section}
Structure your answer as follows:

1. DIRECT ANSWER: Answer the query immediately with the specific section, clause, or article name.

2. LEGAL BASIS: Cite the exact law, section number, and what it says. Example: "Section 27, Indian Contract Act 1872 states..."

3. CASE LAW: Mention one relevant court judgment if applicable. Example: "The Supreme Court in [Case Name] (Year) held that..."

4. ACTIONABLE STEP: Tell the person exactly what to do next. Be specific (e.g., "File an FIR at your local police station", "Call 1930 for cyber fraud").

5. WHERE TO VERIFY: Provide one relevant link such as https://indiankanoon.org, https://cybercrime.gov.in, https://consumerhelpline.gov.in, https://nalsa.gov.in, or the relevant government portal.

{("6. RISK LEVEL: " + risk.get("level","MEDIUM") + " - " + risk.get("recommendation","Review recommended.")) if is_scenario else ""}

Note: This is for informational purposes only and does not constitute legal advice. Please consult a qualified lawyer for specific guidance.

Answer:"""

        final = await self.llm.generate(prompt, temperature=0.1, max_tokens=1024)
        validated = self.guardrails.validate_output(final)
        state["final_answer"] = validated["answer"]
        return state

    def _route_after_lawyers(self, state) -> str:
        q = state["query"].lower()
        if any(w in q for w in ["draft", "letter", "notice", "agreement", "generate"]):
            return "draft"
        if state.get("risk_score", {}).get("level") in ["HIGH", "CRITICAL"]:
            return "human"
        return "synthesize"

    def _detect_practice_area(self, query: str) -> str:
        q = query.lower()
        if "contract" in q or "agreement" in q:
            return "Contract Law"
        elif "employment" in q or "employee" in q or "labour" in q:
            return "Employment Law"
        elif "tenant" in q or "rent" in q or "lease" in q:
            return "Property Law"
        elif "data" in q or "privacy" in q or "gdpr" in q:
            return "Data Privacy Law"
        elif "consumer" in q:
            return "Consumer Law"
        elif "patent" in q or "trademark" in q or "ip" in q:
            return "Intellectual Property"
        return "General Corporate Law"

    async def run(self, query: str, jurisdiction: str = "India") -> Dict:
        guard = self.guardrails.validate_input(query)
        if not guard["valid"]:
            return {"error": guard["reason"], "final_answer": guard["reason"]}
        state: OrchestratorState = {
            "query": query, "jurisdiction": jurisdiction,
            "documents": [], "retrieved_chunks": [], "rag_strategy": "",
            "mcts_path": [], "autogen_analysis": {}, "crew_analysis": {},
            "final_answer": "", "citations": [], "risk_score": {},
            "contradictions": [], "similar_cases": [], "lawyers": [],
            "needs_human": False, "draft": "", "error": None,
        }
        try:
            if self.graph:
                return await self.graph.ainvoke(state)
            return await self._sequential_run(state)
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            state["error"] = str(e)
            state["final_answer"] = f"Analysis failed: {str(e)}"
            return state

    async def _sequential_run(self, state):
        for step in [
            self.retrieve_documents, self.mcts_planning, self.autogen_analysis,
            self.crew_analysis, self.find_contradictions, self.assess_risks,
            self.suggest_lawyers,
        ]:
            state = await step(state)
        if self._route_after_lawyers(state) == "draft":
            state = await self.generate_draft(state)
        state = await self.human_validation(state)
        state = await self.synthesize_final(state)
        return state
