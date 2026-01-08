import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
db = create_client(url, key)

# Query component_catalog directly
result = db.table("component_catalog").select("*").limit(30).execute()
items = result.data

print(f"Total items in component_catalog: {len(items)}")
print("---")

if items:
    # Group by type
    types = {}
    for item in items:
        t = item.get('type', 'unknown')
        if t not in types:
            types[t] = []
        types[t].append(item)
    
    for t, items_list in types.items():
        print(f"\n{t.upper()} ({len(items_list)}):")
        for item in items_list[:5]:
            ext_ids = []
            if item.get('uniprot_accession'):
                ext_ids.append(f"UniProt:{item['uniprot_accession']}")
            if item.get('pubchem_cid'):
                ext_ids.append(f"PubChem:{item['pubchem_cid']}")
            if item.get('chembl_id'):
                ext_ids.append(f"ChEMBL:{item['chembl_id']}")
            id_str = ', '.join(ext_ids) if ext_ids else 'No external IDs'
            gold = "[GOLD]" if item.get('is_gold') else ""
            print(f"  - {item['name']} {gold}: {id_str}")
else:
    print("No items found. Migration may not be applied yet.")
    
    # Check if table exists with the new columns
    try:
        test = db.table("component_catalog").select("is_gold").limit(1).execute()
        print("\nColumn 'is_gold' exists - migration applied.")
    except Exception as e:
        print(f"\nColumn 'is_gold' does not exist: {e}")
        print("Please apply migration: infra/supabase/migrations/004_refine_catalog_schema.sql")
