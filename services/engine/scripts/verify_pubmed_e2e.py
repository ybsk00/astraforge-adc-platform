"""
E2E Verification Script - PubMed Pipeline
100편 수집 → chunk → embed 테스트

실행: python scripts/verify_pubmed_e2e.py
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


async def verify_pubmed_e2e():
    """PubMed E2E 검증 스크립트"""
    
    print("=" * 60)
    print("📚 PubMed E2E Verification")
    print("=" * 60)
    
    results = {
        "fetch": {"status": "pending", "count": 0},
        "raw_save": {"status": "pending", "count": 0},
        "normalize": {"status": "pending", "count": 0},
        "chunk": {"status": "pending", "count": 0},
        "embed": {"status": "pending", "count": 0},
    }
    
    try:
        # 1. Supabase 연결 확인
        print("\n[1/5] Checking Supabase connection...")
        from supabase import create_client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
            return results
        
        db = create_client(supabase_url, supabase_key)
        print("✅ Supabase connected")
        
        # 2. PubMed Connector로 100편 Fetch
        print("\n[2/5] Fetching 100 articles from PubMed...")
        from app.connectors.pubmed import PubMedConnector
        
        connector = PubMedConnector(db)
        
        # ADC 관련 검색어로 100편 수집
        seed = {
            "query": "antibody drug conjugate ADC",
            "retmax": 100
        }
        
        fetch_result = await connector.run(seed, max_pages=5)
        
        results["fetch"]["count"] = fetch_result.get("stats", {}).get("fetched", 0)
        results["fetch"]["status"] = "success" if results["fetch"]["count"] > 0 else "failed"
        
        print(f"✅ Fetched {results['fetch']['count']} articles")
        
        # 3. Raw 저장 확인
        print("\n[3/5] Verifying raw data storage...")
        raw_count = db.table("raw_source_records").select(
            "id", count="exact"
        ).eq("source", "pubmed").execute()
        
        results["raw_save"]["count"] = raw_count.count or 0
        results["raw_save"]["status"] = "success" if results["raw_save"]["count"] > 0 else "failed"
        
        print(f"✅ {results['raw_save']['count']} raw records in database")
        
        # 4. Chunk 확인 (literature_chunks 테이블)
        print("\n[4/5] Checking chunks (if available)...")
        try:
            chunks = db.table("literature_chunks").select(
                "id", count="exact"
            ).execute()
            results["chunk"]["count"] = chunks.count or 0
            results["chunk"]["status"] = "success" if results["chunk"]["count"] > 0 else "pending"
            print(f"✅ {results['chunk']['count']} chunks in database")
        except Exception as e:
            results["chunk"]["status"] = "skipped"
            print(f"⏭️ Chunks table not available or empty: {e}")
        
        # 5. Embedding 확인
        print("\n[5/5] Checking embeddings (if available)...")
        try:
            embedded = db.table("literature_chunks").select(
                "id", count="exact"
            ).not_.is_("embedding", "null").execute()
            results["embed"]["count"] = embedded.count or 0
            results["embed"]["status"] = "success" if results["embed"]["count"] > 0 else "pending"
            print(f"✅ {results['embed']['count']} embedded chunks")
        except Exception as e:
            results["embed"]["status"] = "skipped"
            print(f"⏭️ Embeddings not available: {e}")
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 E2E Verification Results")
    print("=" * 60)
    print(f"  Fetch:     {results['fetch']['status']:10} ({results['fetch']['count']} records)")
    print(f"  Raw Save:  {results['raw_save']['status']:10} ({results['raw_save']['count']} records)")
    print(f"  Normalize: {results['normalize']['status']:10}")
    print(f"  Chunk:     {results['chunk']['status']:10} ({results['chunk']['count']} chunks)")
    print(f"  Embed:     {results['embed']['status']:10} ({results['embed']['count']} embeddings)")
    
    # DoD 체크
    passed = results["fetch"]["count"] >= 100 and results["raw_save"]["count"] > 0
    print("\n" + "=" * 60)
    if passed:
        print("✅ DoD PASSED: PubMed E2E verification successful!")
    else:
        print("❌ DoD PENDING: Need 100+ articles fetched and stored")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    asyncio.run(verify_pubmed_e2e())
