# Create clear_pinecone.py
from pinecone import Pinecone
import os
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("legal-advisor")

# Delete all vectors
index.delete(delete_all=True)
print("All vectors deleted from Pinecone")


# create clear_supabase.py
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
supabase.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
print("All documents deleted from Supabase")