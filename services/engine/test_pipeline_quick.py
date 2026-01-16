import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client
from app.services.pipeline import PipelineService


async def test_pipeline_quick():
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    db = create_client(url, key)

    # 임시 Seed Set 생성 (테스트용)
    # 실제 DB의 데이터를 사용하되, 쿼리 수를 제한하기 위해 PipelineService를 약간 수정하거나
    # 테스트용 Seed Set을 DB에 직접 만듭니다.

    # 여기서는 기존 Seed Set을 사용하되, PubMedConnector의 build_queries를 모킹하거나
    # 그냥 실행하고 결과를 기다립니다. (max_pages=1이면 금방 끝날 것임)

    seed_sets = db.table("seed_sets").select("id").limit(1).execute()
    seed_set_id = seed_sets.data[0]["id"]

    print(f"Testing Pipeline Quick with Seed Set ID: {seed_set_id}")

    pipeline = PipelineService(db)

    # 오직 opentargets만 실행 (PubMed는 너무 많음)
    result = await pipeline.run_seed_set(
        seed_set_id=seed_set_id, connector_names=["opentargets"], max_pages=1
    )

    print("\nPipeline Execution Result (Open Targets Only):")
    print(f"  Status: {result['status']}")
    print(f"  Resolution Stats: {result['resolution_stats']}")
    print("  Connector Results:")
    for name, res in result["results"].items():
        print(
            f"    - {name}: {res.get('status')} (Fetched: {res.get('stats', {}).get('fetched', 0)})"
        )


if __name__ == "__main__":
    asyncio.run(test_pipeline_quick())
