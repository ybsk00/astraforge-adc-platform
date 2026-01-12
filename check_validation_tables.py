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

print("--- Checking Validation Tables ---")
try:
    # Try to select from golden_validation_runs
    response = supabase.table("golden_validation_runs").select("*").limit(1).execute()
    print("✅ Table 'golden_validation_runs' exists.")
except Exception as e:
    print(f"❌ Table 'golden_validation_runs' check failed: {e}")

try:
    # Try to select from golden_validation_metrics
    response = supabase.table("golden_validation_metrics").select("*").limit(1).execute()
    print("✅ Table 'golden_validation_metrics' exists.")
except Exception as e:
    print(f"❌ Table 'golden_validation_metrics' check failed: {e}")
