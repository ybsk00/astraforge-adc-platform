import os
import json
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: Missing env vars")
    exit(1)

supabase = create_client(url, key)

print("--- Populating Dashboard Data ---")

try:
    # 1. Create a Validation Run
    run_data = {
        "pass": True,
        "scoring_version": "v1.0",
        "dataset_version": "v1",
        "created_at": datetime.now().isoformat()
    }
    
    print("Inserting validation run...")
    run_res = supabase.table("golden_validation_runs").insert(run_data).select().execute()
    
    if not run_res.data:
        print("Failed to insert run")
        exit(1)
        
    run_id = run_res.data[0]['id']
    print(f"Run ID: {run_id}")

    # 2. Insert Metrics
    metrics_data = [
        {"run_id": run_id, "axis": "overall", "metric": "MAE", "value": 0.12},
        {"run_id": run_id, "axis": "overall", "metric": "Spearman", "value": 0.85},
        {"run_id": run_id, "axis": "overall", "metric": "TopKOverlap", "value": 0.9},
        
        {"run_id": run_id, "axis": "Bio", "metric": "MAE", "value": 0.15},
        {"run_id": run_id, "axis": "Bio", "metric": "Spearman", "value": 0.82},
        
        {"run_id": run_id, "axis": "Safety", "metric": "MAE", "value": 0.08},
        {"run_id": run_id, "axis": "Safety", "metric": "Spearman", "value": 0.88},
        
        {"run_id": run_id, "axis": "Eng", "metric": "MAE", "value": 0.10},
        {"run_id": run_id, "axis": "Eng", "metric": "Spearman", "value": 0.86},
    ]
    
    print("Inserting metrics...")
    supabase.table("golden_validation_metrics").insert(metrics_data).execute()
    
    print("✅ Dashboard data populated successfully!")

except Exception as e:
    print(f"Error: {e}")
