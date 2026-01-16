"""
E2E Verification Script - UniProt Target Profiles
seed 20개로 target_profiles 생성 확인

실행: python scripts/verify_uniprot_e2e.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


# ADC 관련 주요 타겟 20개
SEED_TARGETS = [
    # HER2 family
    {"uniprot_id": "P04626", "name": "ERBB2 (HER2)"},
    {"uniprot_id": "P00533", "name": "EGFR (HER1)"},
    {"uniprot_id": "P21860", "name": "ERBB3 (HER3)"},
    {"uniprot_id": "Q15303", "name": "ERBB4 (HER4)"},
    # Blood cancers
    {"uniprot_id": "P11836", "name": "CD20 (MS4A1)"},
    {"uniprot_id": "P08637", "name": "CD19"},
    {"uniprot_id": "P20963", "name": "CD3"},
    {"uniprot_id": "Q02223", "name": "TNFRSF8 (CD30)"},
    # Solid tumors
    {"uniprot_id": "P16422", "name": "EPCAM"},
    {"uniprot_id": "P48061", "name": "CXCL12"},
    {"uniprot_id": "Q99808", "name": "SLC7A5 (LAT1)"},
    {"uniprot_id": "P07858", "name": "CTSB (Cathepsin B)"},
    # Immune checkpoint
    {"uniprot_id": "Q15116", "name": "PDCD1 (PD-1)"},
    {"uniprot_id": "Q9NZQ7", "name": "CD274 (PD-L1)"},
    {"uniprot_id": "P16410", "name": "CTLA4"},
    # Additional targets
    {"uniprot_id": "P35968", "name": "KDR (VEGFR2)"},
    {"uniprot_id": "P17948", "name": "FLT1 (VEGFR1)"},
    {"uniprot_id": "Q16288", "name": "NTRK1 (TrkA)"},
    {"uniprot_id": "P04637", "name": "TP53"},
    {"uniprot_id": "Q01196", "name": "RUNX1"},
]


async def verify_uniprot_e2e():
    """UniProt E2E 검증 스크립트"""

    print("=" * 60)
    print("🧬 UniProt Target Profiles E2E Verification")
    print("=" * 60)

    results = {
        "total_seeds": len(SEED_TARGETS),
        "fetched": 0,
        "profiles_created": 0,
        "profiles_updated": 0,
        "errors": 0,
        "details": [],
    }

    try:
        # 1. Supabase 연결
        print("\n[1/3] Checking Supabase connection...")
        from supabase import create_client

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            print("❌ SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
            return results

        db = create_client(supabase_url, supabase_key)
        print("✅ Supabase connected")

        # 2. UniProt Connector로 20개 타겟 Fetch
        print(f"\n[2/3] Fetching {len(SEED_TARGETS)} targets from UniProt...")
        from app.connectors.uniprot import UniProtConnector

        connector = UniProtConnector(db)

        uniprot_ids = [t["uniprot_id"] for t in SEED_TARGETS]
        seed = {"uniprot_ids": uniprot_ids}

        fetch_result = await connector.run(seed, max_pages=1)

        stats = fetch_result.get("stats", {})
        results["fetched"] = stats.get("fetched", 0)
        results["profiles_created"] = stats.get("new", 0)
        results["profiles_updated"] = stats.get("updated", 0)
        results["errors"] = stats.get("errors", 0)

        print(f"✅ Fetched: {results['fetched']}")
        print(f"✅ New profiles: {results['profiles_created']}")
        print(f"✅ Updated profiles: {results['profiles_updated']}")

        # 3. target_profiles 확인
        print("\n[3/3] Verifying target_profiles in database...")

        for target in SEED_TARGETS:
            profile = (
                db.table("target_profiles")
                .select("id, gene_symbol, protein_name, updated_at")
                .eq("uniprot_id", target["uniprot_id"])
                .execute()
            )

            if profile.data:
                p = profile.data[0]
                results["details"].append(
                    {
                        "uniprot_id": target["uniprot_id"],
                        "name": target["name"],
                        "status": "found",
                        "gene_symbol": p.get("gene_symbol"),
                        "protein_name": p.get("protein_name", "")[:30],
                    }
                )
                print(f"  ✅ {target['uniprot_id']}: {p.get('gene_symbol', 'N/A')}")
            else:
                results["details"].append(
                    {
                        "uniprot_id": target["uniprot_id"],
                        "name": target["name"],
                        "status": "not_found",
                    }
                )
                print(f"  ❌ {target['uniprot_id']}: Not found")

    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback

        traceback.print_exc()

    # 결과 요약
    found_count = len([d for d in results["details"] if d["status"] == "found"])

    print("\n" + "=" * 60)
    print("📊 E2E Verification Results")
    print("=" * 60)
    print(f"  Total Seeds:    {results['total_seeds']}")
    print(f"  Fetched:        {results['fetched']}")
    print(f"  Created:        {results['profiles_created']}")
    print(f"  Updated:        {results['profiles_updated']}")
    print(f"  Found in DB:    {found_count}/{len(SEED_TARGETS)}")
    print(f"  Errors:         {results['errors']}")

    # DoD 체크
    passed = found_count >= 20
    print("\n" + "=" * 60)
    if passed:
        print("✅ DoD PASSED: UniProt target profiles verification successful!")
    else:
        print(f"❌ DoD PENDING: Need 20 target_profiles, found {found_count}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(verify_uniprot_e2e())
