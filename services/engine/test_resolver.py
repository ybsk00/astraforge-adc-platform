import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client
from app.services.resolver import ResolverService

async def test_resolver():
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    db = create_client(url, key)
    
    # 첫 번째 Seed Set ID 가져오기
    seed_sets = db.table("seed_sets").select("id").limit(1).execute()
    if not seed_sets.data:
        print("No seed sets found in DB.")
        return
    
    seed_set_id = seed_sets.data[0]["id"]
    print(f"Testing Resolver with Seed Set ID: {seed_set_id}")
    
    resolver = ResolverService(db)
    
    # resolve_seed_set 테스트
    result = await resolver.resolve_seed_set(seed_set_id)
    
    print(f"\nResolution Result:")
    print(f"  Status: {result['status']}")
    print(f"  Stats: {result['stats']}")
    
    # DB 업데이트 확인
    targets = db.table("seed_set_targets").select("entity_targets(*)").eq("seed_set_id", seed_set_id).limit(5).execute()
    print("\nUpdated Targets (Sample):")
    for row in targets.data:
        t = row.get("entity_targets")
        print(f"  - {t['gene_symbol']}: {t.get('ensembl_gene_id', 'Not Resolved')}")

    diseases = db.table("seed_set_diseases").select("entity_diseases(*)").eq("seed_set_id", seed_set_id).limit(5).execute()
    print("\nUpdated Diseases (Sample):")
    for row in diseases.data:
        d = row.get("entity_diseases")
        print(f"  - {d['disease_name']}: {d.get('ontology_id', 'Not Resolved')}")

if __name__ == "__main__":
    asyncio.run(test_resolver())
