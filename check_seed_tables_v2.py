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
    "entity_drugs",
    "seed_sets",
    "seed_set_targets",
    "seed_set_diseases",
    "seed_set_drugs"
]

print("--- Table Counts ---")
for table in tables:
    try:
        result = db.table(table).select("count", count="exact").execute()
        print(f"{table}: {result.count}")
    except Exception as e:
        print(f"{table}: Error - {e}")

print("\n--- Seed Sets ---")
try:
    result = db.table("seed_sets").select("*").execute()
    for row in result.data:
        print(f"ID: {row['id']}, Name: {row['seed_set_name']}")
except Exception as e:
    print(f"Error: {e}")
