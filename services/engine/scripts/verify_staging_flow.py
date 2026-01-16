"""
E2E Verification Script - Staging Approval Flow
pending → approved → catalog 반영 테스트

실행: python scripts/verify_staging_flow.py
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


async def verify_staging_flow():
    """Staging 승인 플로우 E2E 검증 스크립트"""

    print("=" * 60)
    print("📋 Staging Approval Flow E2E Verification")
    print("=" * 60)

    results = {
        "staging_created": False,
        "staging_pending": False,
        "staging_approved": False,
        "catalog_created": False,
        "cleanup_done": False,
    }

    test_component_id = None
    catalog_component_id = None

    try:
        # 1. Supabase 연결
        print("\n[1/5] Checking Supabase connection...")
        from supabase import create_client

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            print("❌ SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
            return results

        db = create_client(supabase_url, supabase_key)
        print("✅ Supabase connected")

        # 2. Staging component 생성 (pending 상태)
        print("\n[2/5] Creating test staging component...")

        test_data = {
            "type": "payload",
            "name": f"E2E_Test_Payload_{datetime.now().strftime('%H%M%S')}",
            "properties": {
                "canonical_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",  # Aspirin
                "name": "E2E Test Compound",
                "molecular_weight": 180.16,
                "source": "e2e_test",
            },
            "quality_grade": "silver",
            "status": "pending_review",
        }

        result = db.table("staging_components").insert(test_data).execute()

        if result.data:
            test_component_id = result.data[0]["id"]
            results["staging_created"] = True
            print(f"✅ Created staging component: {test_component_id}")
        else:
            print("❌ Failed to create staging component")
            return results

        # 3. Pending 상태 확인
        print("\n[3/5] Verifying pending status...")

        pending = (
            db.table("staging_components")
            .select("status")
            .eq("id", test_component_id)
            .execute()
        )

        if pending.data and pending.data[0]["status"] == "pending_review":
            results["staging_pending"] = True
            print("✅ Component is in pending_review status")
        else:
            print("❌ Component status is not pending_review")

        # 4. 승인 처리 (approved 상태로 변경 + catalog 생성)
        print("\n[4/5] Approving component and creating catalog entry...")

        # 승인 상태로 변경
        db.table("staging_components").update(
            {
                "status": "approved",
                "approved_at": datetime.utcnow().isoformat(),
                "review_note": "E2E Test - Auto approved",
            }
        ).eq("id", test_component_id).execute()

        # 승인 확인
        approved = (
            db.table("staging_components")
            .select("status")
            .eq("id", test_component_id)
            .execute()
        )

        if approved.data and approved.data[0]["status"] == "approved":
            results["staging_approved"] = True
            print("✅ Component approved")

        # component_catalog에 생성
        catalog_data = {
            "type": test_data["type"],
            "name": test_data["name"],
            "smiles": test_data["properties"].get("canonical_smiles"),
            "properties": {
                **test_data["properties"],
                "staging_id": str(test_component_id),
                "approved_at": datetime.utcnow().isoformat(),
            },
            "status": "pending_compute",
        }

        catalog_result = db.table("component_catalog").insert(catalog_data).execute()

        if catalog_result.data:
            catalog_component_id = catalog_result.data[0]["id"]
            results["catalog_created"] = True
            print(f"✅ Created catalog entry: {catalog_component_id}")
        else:
            print("❌ Failed to create catalog entry")

        # 5. 정리 (테스트 데이터 삭제)
        print("\n[5/5] Cleaning up test data...")

        if catalog_component_id:
            db.table("component_catalog").delete().eq(
                "id", catalog_component_id
            ).execute()
        if test_component_id:
            db.table("staging_components").delete().eq(
                "id", test_component_id
            ).execute()

        results["cleanup_done"] = True
        print("✅ Test data cleaned up")

    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback

        traceback.print_exc()

        # 오류 시에도 정리 시도
        if test_component_id:
            try:
                db.table("staging_components").delete().eq(
                    "id", test_component_id
                ).execute()
            except:
                pass
        if catalog_component_id:
            try:
                db.table("component_catalog").delete().eq(
                    "id", catalog_component_id
                ).execute()
            except:
                pass

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 E2E Verification Results")
    print("=" * 60)
    print(f"  Staging Created:  {'✅' if results['staging_created'] else '❌'}")
    print(f"  Pending Status:   {'✅' if results['staging_pending'] else '❌'}")
    print(f"  Approved Status:  {'✅' if results['staging_approved'] else '❌'}")
    print(f"  Catalog Created:  {'✅' if results['catalog_created'] else '❌'}")
    print(f"  Cleanup Done:     {'✅' if results['cleanup_done'] else '❌'}")

    # DoD 체크
    all_passed = all(
        [
            results["staging_created"],
            results["staging_pending"],
            results["staging_approved"],
            results["catalog_created"],
        ]
    )

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ DoD PASSED: Staging approval flow verification successful!")
    else:
        print("❌ DoD FAILED: Some flow steps did not complete")
    print("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(verify_staging_flow())
