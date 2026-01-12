import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: Missing env vars")
    exit(1)

print(f"Connecting to {url}...")
supabase = create_client(url, key)

try:
    # Check if 'result_summary' column exists in 'connector_runs'
    # We can check this by trying to select it from a limit 1 query
    print("Checking 'connector_runs' schema...")
    try:
        # Try to select the specific column
        supabase.table("connector_runs").select("result_summary").limit(1).execute()
        print("✅ Column 'result_summary' exists!")
    except Exception as e:
        print(f"❌ Column 'result_summary' check failed: {e}")
        print("   -> Please run '013_add_result_summary.sql' in Supabase SQL Editor.")

except Exception as e:
    print(f"Verification Failed: {e}")
