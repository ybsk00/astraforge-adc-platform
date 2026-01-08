"""
DoD (Definition of Done) Master Verification Script
전체 DoD 항목을 순차적으로 검증

실행: python scripts/verify_dod.py
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


async def run_all_verifications():
    """전체 DoD 검증 실행"""
    
    print("=" * 70)
    print("🎯 ADC Platform - DoD (Definition of Done) Verification")
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    dod_results = {
        "connector_framework": {"status": "pending", "details": ""},
        "pubmed_e2e": {"status": "pending", "details": ""},
        "uniprot_e2e": {"status": "pending", "details": ""},
        "staging_flow": {"status": "pending", "details": ""},
        "observability": {"status": "pending", "details": ""},
        "retry_button": {"status": "pending", "details": ""},
    }
    
    try:
        from supabase import create_client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            print("\n❌ Environment variables not set!")
            print("   Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
            return dod_results
        
        db = create_client(supabase_url, supabase_key)
        
        # 1. Connector Framework
        print("\n" + "-" * 50)
        print("📦 [1/6] Connector Framework Check")
        print("-" * 50)
        
        try:
            from app.connectors.base import BaseConnector, RateLimiter, generate_query_hash
            from app.connectors.pubmed import PubMedConnector
            from app.connectors.uniprot import UniProtConnector
            
            dod_results["connector_framework"]["status"] = "passed"
            dod_results["connector_framework"]["details"] = "All connectors importable"
            print("✅ Connector framework verified")
        except Exception as e:
            dod_results["connector_framework"]["status"] = "failed"
            dod_results["connector_framework"]["details"] = str(e)
            print(f"❌ Connector framework error: {e}")
        
        # 2. PubMed E2E (간략 체크)
        print("\n" + "-" * 50)
        print("📚 [2/6] PubMed E2E Check")
        print("-" * 50)
        
        try:
            raw_count = db.table("raw_source_records").select(
                "id", count="exact"
            ).eq("source", "pubmed").execute()
            
            count = raw_count.count or 0
            if count >= 100:
                dod_results["pubmed_e2e"]["status"] = "passed"
                dod_results["pubmed_e2e"]["details"] = f"{count} records"
            else:
                dod_results["pubmed_e2e"]["status"] = "partial"
                dod_results["pubmed_e2e"]["details"] = f"{count}/100 records"
            
            print(f"  PubMed records: {count}")
        except Exception as e:
            dod_results["pubmed_e2e"]["status"] = "skipped"
            dod_results["pubmed_e2e"]["details"] = str(e)[:50]
            print(f"⏭️ PubMed check skipped: {e}")
        
        # 3. UniProt E2E (간략 체크)
        print("\n" + "-" * 50)
        print("🧬 [3/6] UniProt E2E Check")
        print("-" * 50)
        
        try:
            profiles = db.table("target_profiles").select(
                "id", count="exact"
            ).execute()
            
            count = profiles.count or 0
            if count >= 20:
                dod_results["uniprot_e2e"]["status"] = "passed"
                dod_results["uniprot_e2e"]["details"] = f"{count} profiles"
            else:
                dod_results["uniprot_e2e"]["status"] = "partial"
                dod_results["uniprot_e2e"]["details"] = f"{count}/20 profiles"
            
            print(f"  Target profiles: {count}")
        except Exception as e:
            dod_results["uniprot_e2e"]["status"] = "skipped"
            dod_results["uniprot_e2e"]["details"] = str(e)[:50]
            print(f"⏭️ UniProt check skipped: {e}")
        
        # 4. Staging Flow (테이블 존재 확인)
        print("\n" + "-" * 50)
        print("📋 [4/6] Staging Flow Check")
        print("-" * 50)
        
        try:
            staging = db.table("staging_components").select("id").limit(1).execute()
            catalog = db.table("component_catalog").select("id").limit(1).execute()
            
            dod_results["staging_flow"]["status"] = "passed"
            dod_results["staging_flow"]["details"] = "Tables accessible"
            print("✅ Staging flow tables verified")
        except Exception as e:
            dod_results["staging_flow"]["status"] = "failed"
            dod_results["staging_flow"]["details"] = str(e)[:50]
            print(f"❌ Staging flow error: {e}")
        
        # 5. Observability (로그 테이블 확인)
        print("\n" + "-" * 50)
        print("📊 [5/6] Observability Check")
        print("-" * 50)
        
        try:
            logs = db.table("ingestion_logs").select("id", count="exact").execute()
            cursors = db.table("ingestion_cursors").select("id", count="exact").execute()
            
            log_count = logs.count or 0
            cursor_count = cursors.count or 0
            
            dod_results["observability"]["status"] = "passed"
            dod_results["observability"]["details"] = f"{log_count} logs, {cursor_count} cursors"
            print(f"✅ Logs: {log_count}, Cursors: {cursor_count}")
        except Exception as e:
            dod_results["observability"]["status"] = "failed"
            dod_results["observability"]["details"] = str(e)[:50]
            print(f"❌ Observability error: {e}")
        
        # 6. Retry Button (API 체크)
        print("\n" + "-" * 50)
        print("🔄 [6/6] Retry Button Check")
        print("-" * 50)
        
        try:
            from app.api.connectors import router
            
            # 라우터에 retry 엔드포인트가 있는지 확인
            routes = [r.path for r in router.routes]
            has_retry = any("retry" in r for r in routes)
            
            if has_retry:
                dod_results["retry_button"]["status"] = "passed"
                dod_results["retry_button"]["details"] = "Retry endpoint available"
                print("✅ Retry endpoint verified")
            else:
                dod_results["retry_button"]["status"] = "partial"
                dod_results["retry_button"]["details"] = "No retry endpoint found"
                print("⚠️ Retry endpoint not found")
        except Exception as e:
            dod_results["retry_button"]["status"] = "skipped"
            dod_results["retry_button"]["details"] = str(e)[:50]
            print(f"⏭️ Retry check skipped: {e}")
            
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
    
    # 최종 결과
    print("\n" + "=" * 70)
    print("📊 DoD Verification Summary")
    print("=" * 70)
    
    status_emoji = {
        "passed": "✅",
        "partial": "🔶",
        "failed": "❌",
        "pending": "⏳",
        "skipped": "⏭️"
    }
    
    passed_count = 0
    total_count = len(dod_results)
    
    for item, result in dod_results.items():
        emoji = status_emoji.get(result["status"], "❓")
        print(f"  {emoji} {item}: {result['status']} - {result['details']}")
        if result["status"] == "passed":
            passed_count += 1
    
    print("\n" + "-" * 70)
    print(f"  Total: {passed_count}/{total_count} passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL DoD CRITERIA PASSED!")
    elif passed_count >= 4:
        print("\n🔶 MOSTLY PASSED - Some items need attention")
    else:
        print("\n❌ DoD NOT MET - Please review and fix issues")
    
    print("=" * 70)
    
    return dod_results


if __name__ == "__main__":
    asyncio.run(run_all_verifications())
