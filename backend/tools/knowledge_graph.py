from neo4j import GraphDatabase
from loguru import logger
from typing import List, Dict
from config import settings


def _is_placeholder(value: str) -> bool:
    if not value:
        return True
    bad = ["your-", "placeholder", "example.com", "your-instance"]
    return any(p in value for p in bad)


class KnowledgeGraph:
    def __init__(self):
        self.driver = None
        self.enabled = False

        if _is_placeholder(settings.neo4j_uri) or _is_placeholder(settings.neo4j_password):
            logger.info("Neo4j not configured — knowledge graph disabled (optional)")
            return

        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            self.driver.verify_connectivity()
            self.enabled = True
            logger.info("Neo4j connected")
        except Exception as e:
            logger.warning(f"Neo4j unavailable: {e}")

    def _run(self, query: str, params: Dict = None):
        if not self.enabled:
            return []
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            return []

    def add_document(self, doc_id: str, name: str, doc_type: str):
        if not self.enabled:
            return
        self._run(
            "MERGE (d:Document {id: $id}) SET d.name = $name, d.type = $type",
            {"id": doc_id, "name": name, "type": doc_type},
        )

    def add_party(self, party_name: str, party_type: str, doc_id: str):
        if not self.enabled:
            return
        self._run(
            "MERGE (p:Party {name: $name}) SET p.type = $type WITH p "
            "MATCH (d:Document {id: $doc_id}) MERGE (d)-[:HAS_PARTY]->(p)",
            {"name": party_name, "type": party_type, "doc_id": doc_id},
        )

    def add_clause(self, clause_id: str, clause_type: str, text: str, doc_id: str):
        if not self.enabled:
            return
        self._run(
            "MERGE (c:Clause {id: $id}) SET c.type = $type, c.text = $text WITH c "
            "MATCH (d:Document {id: $doc_id}) MERGE (d)-[:HAS_CLAUSE]->(c)",
            {"id": clause_id, "type": clause_type, "text": text[:500], "doc_id": doc_id},
        )

    def get_document_entities(self, doc_id: str) -> Dict:
        parties = self._run(
            "MATCH (d:Document {id: $id})-[:HAS_PARTY]->(p:Party) RETURN p", {"id": doc_id}
        )
        clauses = self._run(
            "MATCH (d:Document {id: $id})-[:HAS_CLAUSE]->(c:Clause) RETURN c", {"id": doc_id}
        )
        return {"parties": parties, "clauses": clauses}

    def find_related_documents(self, doc_id: str) -> List[Dict]:
        return self._run(
            "MATCH (d1:Document {id: $id})-[:HAS_PARTY]->(p:Party)<-[:HAS_PARTY]-(d2:Document) "
            "WHERE d2.id <> $id RETURN d2, p LIMIT 10",
            {"id": doc_id},
        )

    def close(self):
        if self.driver:
            self.driver.close()
