import math
import random
from typing import List, Dict
from dataclasses import dataclass, field
from config import settings


@dataclass
class MCTSNode:
    query: str
    parent: "MCTSNode" = None
    children: List["MCTSNode"] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0
    action: str = ""
    state: Dict = field(default_factory=dict)


class MCTSPlanner:
    POSSIBLE_ACTIONS = [
        "retrieve_documents", "summarize_clauses", "extract_obligations",
        "check_compliance", "find_contradictions", "assess_risks",
        "search_precedents", "generate_recommendations", "request_human_review",
    ]
    ACTION_REWARDS = {
        "retrieve_documents": 0.9, "summarize_clauses": 0.8,
        "extract_obligations": 0.7, "check_compliance": 0.6,
        "find_contradictions": 0.5, "assess_risks": 0.7,
        "search_precedents": 0.6, "generate_recommendations": 0.9,
        "request_human_review": 0.4,
    }
    KEYWORD_BOOSTS = {
        "find_contradictions": ["conflict", "contradict", "different", "inconsistent"],
        "assess_risks": ["risk", "dangerous", "problem", "liability", "penalty"],
        "search_precedents": ["case", "judgment", "court", "precedent", "ruling"],
        "check_compliance": ["comply", "regulation", "statute", "law", "gdpr"],
        "generate_recommendations": ["recommend", "suggest", "advise"],
    }

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.iterations = settings.mcts_iterations
        self.C = settings.mcts_exploration_constant

    async def search(self, query: str, documents: List[Dict]) -> List[Dict]:
        root = MCTSNode(query=query, state={"documents": documents})
        for _ in range(self.iterations):
            node = self._select(root)
            if node.visits > 0 and not node.children:
                self._expand(node)
            if node.children:
                node = random.choice(node.children)
            reward = self._simulate(node)
            self._backpropagate(node, reward)
        return self._best_path(root)

    def _select(self, node: MCTSNode) -> MCTSNode:
        while node.children:
            unvisited = [c for c in node.children if c.visits == 0]
            if unvisited:
                return random.choice(unvisited)
            node = max(node.children, key=lambda c: self._ucb(c, node.visits))
        return node

    def _ucb(self, child: MCTSNode, parent_visits: int) -> float:
        if child.visits == 0:
            return float("inf")
        return child.value / child.visits + self.C * math.sqrt(math.log(parent_visits) / child.visits)

    def _expand(self, node: MCTSNode):
        for action in self.POSSIBLE_ACTIONS:
            node.children.append(MCTSNode(query=node.query, parent=node, action=action, state=node.state.copy()))

    def _simulate(self, node: MCTSNode) -> float:
        base = self.ACTION_REWARDS.get(node.action, 0.5)
        q = node.query.lower()
        for action, keywords in self.KEYWORD_BOOSTS.items():
            if node.action == action and any(kw in q for kw in keywords):
                base = min(base + 0.3, 1.0)
                break
        return base

    def _backpropagate(self, node: MCTSNode, reward: float):
        while node:
            node.visits += 1
            node.value += reward
            node = node.parent

    def _best_path(self, root: MCTSNode) -> List[Dict]:
        path = []
        cur = root
        while cur.children:
            best = max(cur.children, key=lambda c: c.value / c.visits if c.visits > 0 else 0)
            path.append({
                "action": best.action,
                "value": round(best.value / best.visits, 4) if best.visits > 0 else 0,
                "visits": best.visits,
            })
            cur = best
        return path
