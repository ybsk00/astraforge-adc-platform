import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

def run_connector(source, batch_mode=False):
    """Run a connector and wait for completion"""
    print(f"\n{'='*50}")
    print(f"Running {source.upper()} Connector (batch_mode={batch_mode})")
    print('='*50)
    
    r = requests.post(f"{BASE_URL}/connectors/{source}/run", json={"batch_mode": batch_mode})
    if r.status_code != 200:
        print(f"  ERROR: {r.status_code} - {r.text}")
        return False
    
    result = r.json()
    print(f"  Job ID: {result.get('job_id', 'N/A')}")
    print(f"  Status: {result.get('status', 'N/A')}")
    
    # Wait for job completion
    time.sleep(3)
    
    # Check connector status
    r = requests.get(f"{BASE_URL}/connectors/{source}/status")
    if r.status_code == 200:
        status = r.json()
        print(f"  Final Status: {status.get('status', 'N/A')}")
        stats = status.get('stats', {})
        if stats:
            print(f"  Stats: fetched={stats.get('fetched', 0)}, new={stats.get('new', 0)}, updated={stats.get('updated', 0)}")
    
    return True

def check_catalog_stats():
    """Check catalog statistics"""
    import os
    from dotenv import load_dotenv
    from supabase import create_client
    
    load_dotenv()
    db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    
    # Count by type
    result = db.table("component_catalog").select("type").execute()
    items = result.data
    
    types = {}
    ext_ids = {"uniprot": 0, "pubchem": 0, "chembl": 0}
    gold_count = 0
    
    for item in items:
        t = item.get('type', 'unknown')
        types[t] = types.get(t, 0) + 1
    
    # Check external IDs
    result = db.table("component_catalog").select("uniprot_accession, pubchem_cid, chembl_id, is_gold").execute()
    for item in result.data:
        if item.get('uniprot_accession'):
            ext_ids["uniprot"] += 1
        if item.get('pubchem_cid'):
            ext_ids["pubchem"] += 1
        if item.get('chembl_id'):
            ext_ids["chembl"] += 1
        if item.get('is_gold'):
            gold_count += 1
    
    print("\n" + "="*50)
    print("CATALOG STATISTICS")
    print("="*50)
    print(f"Total Items: {len(items)}")
    print(f"Gold Standard: {gold_count}")
    print("\nBy Type:")
    for t, count in types.items():
        print(f"  - {t}: {count}")
    print("\nExternal IDs Resolved:")
    for src, count in ext_ids.items():
        print(f"  - {src}: {count}")
    
    return types, ext_ids, gold_count

print("="*60)
print("DOMAIN DATA AUTOMATION - FULL PIPELINE TEST")
print("="*60)

# Step 1: Check current state
print("\n[STEP 1] Current Catalog State:")
types, ext_ids, gold = check_catalog_stats()

# Step 2: Run Resolve Job (to ensure IDs are filled)
run_connector("resolve")

# Step 3: Run Batch Fetchers
time.sleep(2)
run_connector("uniprot", batch_mode=True)
time.sleep(2)
run_connector("chembl", batch_mode=True)
time.sleep(2)
run_connector("pubchem", batch_mode=True)

# Step 4: Final State
time.sleep(5)
print("\n[STEP 4] Final Catalog State After Enrichment:")
types, ext_ids, gold = check_catalog_stats()

print("\n" + "="*60)
print("PIPELINE TEST COMPLETE")
print("="*60)
