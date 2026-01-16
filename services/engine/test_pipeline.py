import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client
from app.services.pipeline import PipelineService


async def test_pipeline():
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
    print(f"Testing Pipeline with Seed Set ID: {seed_set_id}")

    pipeline = PipelineService(db)

    # run_seed_set 테스트 (속도를 위해 max_pages=1로 설정)
    result = await pipeline.run_seed_set(
        seed_set_id=seed_set_id, connector_names=["pubmed", "opentargets"], max_pages=1
    )

    print("\nPipeline Execution Result:")
    print(f"  Status: {result['status']}")
    print(f"  Resolution Stats: {result['resolution_stats']}")
    print("  Connector Results:")
    for name, res in result["results"].items():
        print(
            f"    - {name}: {res.get('status')} (Fetched: {res.get('stats', {}).get('fetched', 0)})"
        )


if __name__ == "__main__":
    asyncio.run(test_pipeline())
