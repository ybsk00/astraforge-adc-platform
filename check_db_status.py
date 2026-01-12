import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: Missing env vars")
    exit(1)

supabase = create_client(url, key)

print("--- Connectors Table ---")
try:
    response = supabase.table("connectors").select("*").execute()
    for row in response.data:
        print(f"Name: {row.get('name')}, Type: {row.get('type')}, Active: {row.get('is_active')}")
except Exception as e:
    print(f"Error fetching connectors: {e}")

print("\n--- Golden Sets Table ---")
try:
    response = supabase.table("golden_sets").select("*").execute()
    print(f"Count: {len(response.data)}")
    if response.data:
        print(response.data[0])
except Exception as e:
    print(f"Error fetching golden_sets: {e}")
