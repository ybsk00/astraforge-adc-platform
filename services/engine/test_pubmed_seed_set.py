import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client
from app.connectors.pubmed import PubMedConnector


async def test_pubmed_seed_set():
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
    print(f"Testing with Seed Set ID: {seed_set_id}")

    connector = PubMedConnector(db)

    # build_queries 테스트
    seed = {"seed_set_id": seed_set_id, "retmax": 10}
    queries = await connector.build_queries(seed)

    print(f"\nGenerated {len(queries)} queries:")
    for i, q in enumerate(queries[:5]):
        print(f"  {i + 1}. {q.query}")

    if len(queries) > 5:
        print(f"  ... and {len(queries) - 5} more.")


if __name__ == "__main__":
    asyncio.run(test_pubmed_seed_set())
