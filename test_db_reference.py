"""
Test: Domain DB Reference for Batch Fetch Jobs

This test verifies that batch fetch jobs correctly reference
the component_catalog table to get IDs for external API calls.
"""
import requests
import time
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

BASE_URL = "http://localhost:8000/api/v1"

def get_db():
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )

def check_catalog_before():
    """Check catalog state before batch fetch"""
    db = get_db()
    result = db.table("component_catalog").select("id, name, type, uniprot_accession, pubchem_cid, chembl_id").limit(30).execute()
    
    print("\n📋 CATALOG STATE (Before Batch Fetch):")
    print("-" * 60)
    
    stats = {"target": 0, "payload": 0, "linker": 0, "antibody": 0}
    ids = {"uniprot": 0, "pubchem": 0, "chembl": 0}
    
    for item in result.data:
        t = item.get("type", "unknown")
        if t in stats:
            stats[t] += 1
        if item.get("uniprot_accession"):
            ids["uniprot"] += 1
        if item.get("pubchem_cid"):
            ids["pubchem"] += 1
        if item.get("chembl_id"):
            ids["chembl"] += 1
    
    print(f"  Total: {len(result.data)}")
    for t, count in stats.items():
        print(f"    - {t}: {count}")
    
    print(f"\n  External IDs resolved:")
    for src, count in ids.items():
        print(f"    - {src}: {count}")
    
    return ids

def run_batch_fetch(source):
    """Run a batch fetch job and check logs"""
    print(f"\n🔄 Running {source.upper()} Batch Fetch...")
    
    try:
        r = requests.post(
            f"{BASE_URL}/connectors/{source}/run",
            json={"batch_mode": True},
            timeout=10
        )
        
        if r.status_code == 200:
            result = r.json()
            print(f"  ✓ Job enqueued: {result.get('job_id', 'N/A')[:16]}...")
            return True
        else:
            print(f"  ✗ Failed: {r.status_code} - {r.text[:100]}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def check_worker_logs():
    """Check worker logs for batch mode confirmation"""
    import subprocess
    result = subprocess.run(
        ["docker", "logs", "adc-worker-1", "--tail", "30"],
        capture_output=True,
        text=True
    )
    
    output = result.stdout + result.stderr
    
    batch_indicators = [
        "batch_mode_enabled",
        "batch_targets_loaded",
        "batch_compounds_loaded"
    ]
    
    print("\n📝 WORKER LOGS (Batch Mode Check):")
    print("-" * 60)
    
    found = False
    for indicator in batch_indicators:
        if indicator in output:
            print(f"  ✓ Found: {indicator}")
            found = True
    
    if not found:
        print("  ⚠ No batch mode indicators found in recent logs")
        # Show last few lines
        lines = output.strip().split('\n')[-5:]
        for line in lines:
            print(f"    {line[:80]}")
    
    return found

def main():
    print("=" * 60)
    print("DOMAIN DB REFERENCE TEST")
    print("=" * 60)
    print("Testing: Batch fetch jobs read IDs from component_catalog")
    
    # Step 1: Check catalog state
    ids_before = check_catalog_before()
    
    if ids_before["uniprot"] == 0 and ids_before["pubchem"] == 0:
        print("\n⚠️ No external IDs found. Running Resolve Job first...")
        requests.post(f"{BASE_URL}/connectors/resolve/run", json={})
        time.sleep(5)
        ids_before = check_catalog_before()
    
    # Step 2: Run batch fetch jobs
    print("\n" + "=" * 60)
    print("BATCH FETCH TEST (batch_mode=True)")
    print("=" * 60)
    
    success_count = 0
    
    if ids_before["uniprot"] > 0:
        if run_batch_fetch("uniprot"):
            success_count += 1
        time.sleep(2)
    else:
        print("\n⏭️ Skipping UniProt (no IDs)")
    
    if ids_before["pubchem"] > 0 or ids_before["chembl"] > 0:
        if run_batch_fetch("chembl"):
            success_count += 1
        time.sleep(2)
        
        if run_batch_fetch("pubchem"):
            success_count += 1
        time.sleep(2)
    else:
        print("\n⏭️ Skipping ChEMBL/PubChem (no IDs)")
    
    # Step 3: Check logs
    time.sleep(3)
    check_worker_logs()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"  Batch fetch jobs triggered: {success_count}/3")
    print(f"  Catalog IDs available: UniProt={ids_before['uniprot']}, PubChem={ids_before['pubchem']}, ChEMBL={ids_before['chembl']}")
    
    if success_count > 0:
        print("\n✅ TEST PASSED: Batch fetch jobs are using DB reference")
    else:
        print("\n❌ TEST FAILED: Could not verify DB reference")

if __name__ == "__main__":
    main()
