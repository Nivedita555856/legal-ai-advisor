from supabase import create_client, Client
from loguru import logger
from typing import List, Dict
from config import settings


class SupabaseClient:
    def __init__(self):
        try:
            self.client: Client = create_client(
                settings.supabase_url, settings.supabase_service_key
            )
            logger.info("Supabase connected")
        except Exception as e:
            logger.warning(f"Supabase init skipped: {e}")
            self.client = None

    async def insert_document(self, doc: Dict) -> Dict:
        if not self.client:
            return {}
        try:
            result = self.client.table("documents").insert(doc).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Insert document error: {e}")
            return {}

    async def get_documents(self, limit: int = 50) -> List[Dict]:
        if not self.client:
            return []
        try:
            result = self.client.table("documents").select("*").limit(limit).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Get documents error: {e}")
            return []

    async def insert_analysis(self, analysis: Dict) -> Dict:
        if not self.client:
            return {}
        try:
            result = self.client.table("analyses").insert(analysis).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Insert analysis error: {e}")
            return {}

    async def get_analyses(self, document_id: str = None) -> List[Dict]:
        if not self.client:
            return []
        try:
            query = self.client.table("analyses").select("*")
            if document_id:
                query = query.eq("document_id", document_id)
            result = query.limit(50).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Get analyses error: {e}")
            return []
