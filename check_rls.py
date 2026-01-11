import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
db = create_client(url, key)

tables = [
    "entity_targets",
    "entity_diseases",
    "entity_linkers",
    "entity_drugs",
    "seed_sets",
    "ingestion_cursors",
    "ingestion_logs"
]

print("Checking RLS status:")
for table in tables:
    try:
        # Query pg_tables to see if rowsecurity is enabled
        result = db.rpc("get_table_rls_status", {"table_name": table}).execute()
        print(f"{table}: {result.data}")
    except Exception as e:
        # If RPC doesn't exist, try a different way or just check if anon can read
        print(f"{table}: Error checking RLS - {e}")

print("\nChecking if ANON can read:")
anon_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
anon_db = create_client(url, anon_key)
for table in tables:
    try:
        result = anon_db.table(table).select("count", count="exact").limit(1).execute()
        print(f"{table}: Count={result.count}")
    except Exception as e:
        print(f"{table}: Error - {e}")
