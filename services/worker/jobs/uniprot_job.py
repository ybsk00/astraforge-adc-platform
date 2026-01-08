"""
UniProt Worker Jobs
Target 프로필 동기화 Job 정의
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import structlog
from supabase import create_client, Client
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
def find_env():
    current = Path(__file__).resolve()
    for _ in range(5):
        current = current.parent
        env_path = current / ".env"
        if env_path.exists():
            return str(env_path)
    return ".env"

load_dotenv(find_env())

logger = structlog.get_logger()


def get_supabase() -> Client:
    """Supabase 클라이언트"""
    return create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    )


async def uniprot_fetch_job(ctx, seed: Dict[str, Any]):
    """
    UniProt Target 동기화 Job
    
    Args:
        ctx: Arq 컨텍스트
        seed: 시드 데이터
            - uniprot_ids: UniProt ID 목록
            - gene_symbols: 유전자 심볼 목록
            - query: 검색 쿼리
    
    Returns:
        실행 결과
    """
    logger.info("uniprot_sync_job_started", seed=seed)
    
    db = get_supabase()
    start_time = datetime.utcnow()
    
    # 커서 해시 생성 (inline implementation)
    import hashlib
    
    uniprot_ids = seed.get("uniprot_ids", [])
    gene_symbols = seed.get("gene_symbols", [])
    query = seed.get("query", "")
    
    # Batch Mode: Catalog에서 ID 조회
    if seed.get("batch_mode"):
        logger.info("uniprot_batch_mode_enabled")
        # Fetch targets with uniprot_accession
        targets = db.table("component_catalog").select("uniprot_accession").eq("type", "target").not_.is_("uniprot_accession", "null").execute()
        catalog_ids = [t["uniprot_accession"] for t in targets.data if t.get("uniprot_accession")]
        if catalog_ids:
            uniprot_ids.extend(catalog_ids)
            logger.info("uniprot_batch_targets_loaded", count=len(catalog_ids))
        else:
            logger.warning("uniprot_batch_no_targets_found")
            return {"status": "completed", "message": "No targets with UniProt Accession found in Catalog"}
    
    # 기본 쿼리 설정 (쿼리가 비어있으면 ADC 관련 타겟 검색)
    if not query and not uniprot_ids and not gene_symbols:
        query = "antibody drug conjugate"
    
    query_key = ",".join(uniprot_ids[:5]) or ",".join(gene_symbols[:5]) or query[:50]
    query_hash = hashlib.md5(f"uniprot:{query_key}:{str(seed)}".encode()).hexdigest()[:16]
    
    # 커서 상태 업데이트: running
    db.table("ingestion_cursors").upsert({
        "source": "uniprot",
        "query_hash": query_hash,
        "status": "running",
        "config": seed,
        "updated_at": datetime.utcnow().isoformat()
    }, on_conflict="source,query_hash").execute()
    
    # 로그 시작
    log_id = db.table("ingestion_logs").insert({
        "source": "uniprot",
        "phase": "sync",
        "status": "started",
        "meta": {"seed": seed}
    }).execute().data[0]["id"]
    
    try:
        # UniProt API 호출 (inline implementation)
        import httpx
        import json
        
        base_url = "https://rest.uniprot.org/uniprotkb/search"
        
        # 검색 쿼리 구성
        search_query = ""
        if uniprot_ids:
            search_query = " OR ".join([f"accession:{uid}" for uid in uniprot_ids])
        elif gene_symbols:
            search_query = " OR ".join([f"gene_exact:{sym}" for sym in gene_symbols])
            search_query += " AND organism_id:9606"  # Human only
        else:
            search_query = f"{query} AND organism_id:9606"
            
        params = {
            "query": search_query,
            "format": "json",
            "fields": "accession,id,protein_name,gene_names,organism_name,cc_function,xref_chembl,xref_drugbank",
            "size": 25
        }
        
        fetched_count = 0
        new_count = 0
        updated_count = 0
        
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            fetched_count = len(results)
            
            for item in results:
                primary_accession = item.get("primaryAccession")
                
                # 데이터 추출
                protein_desc = item.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "")
                
                genes = item.get("genes", [])
                gene_symbol = genes[0].get("geneName", {}).get("value", "") if genes else None
                
                comments = item.get("comments", [])
                function_summary = ""
                for comment in comments:
                    if comment.get("commentType") == "FUNCTION":
                        function_summary = comment.get("texts", [])[0].get("value", "")
                        break
                
                organism = item.get("organism", {}).get("scientificName", "Homo sapiens")
                
                # External Refs
                xrefs = {}
                for ref in item.get("uniProtKBCrossReferences", []):
                    db_name = ref.get("database")
                    if db_name in ["ChEMBL", "DrugBank"]:
                        if db_name not in xrefs:
                            xrefs[db_name] = []
                        xrefs[db_name].append(ref.get("id"))
                
                # Raw Data 저장
                payload = item
                checksum = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                
                db.table("raw_source_records").upsert({
                    "source": "uniprot",
                    "external_id": primary_accession,
                    "payload": payload,
                    "checksum": checksum,
                    "fetched_at": datetime.utcnow().isoformat()
                }, on_conflict="source,external_id").execute()
                
                # Target Profile 저장 (Upsert)
                target_data = {
                    "uniprot_id": primary_accession,
                    "gene_symbol": gene_symbol,
                    "protein_name": protein_desc[:500],
                    "function_summary": function_summary[:2000],
                    "organism": organism,
                    "external_refs": xrefs,
                    "checksum": checksum,
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # 기존 데이터 확인
                existing = db.table("target_profiles").select("id").eq("uniprot_id", primary_accession).execute()
                
                if existing.data:
                    db.table("target_profiles").update(target_data).eq("uniprot_id", primary_accession).execute()
                    updated_count += 1
                else:
                    db.table("target_profiles").insert(target_data).execute()
                    new_count += 1
        
        stats = {"fetched": fetched_count, "new": new_count, "updated": updated_count}
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # 커서 상태 업데이트: idle
        db.table("ingestion_cursors").update({
            "status": "idle",
            "last_success_at": datetime.utcnow().isoformat(),
            "stats": stats,
            "error_message": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "uniprot").eq("query_hash", query_hash).execute()
        
        # 로그 완료
        db.table("ingestion_logs").update({
            "status": "completed",
            "duration_ms": duration_ms,
            "records_fetched": stats.get("fetched", 0),
            "records_new": stats.get("new", 0),
            "records_updated": stats.get("updated", 0)
        }).eq("id", log_id).execute()
        
        logger.info("uniprot_sync_job_completed", stats=stats)
        
        return {"status": "completed", "stats": stats, "duration_ms": duration_ms}
        
    except Exception as e:
        logger.error("uniprot_sync_job_failed", error=str(e))
        
        # 커서 상태 업데이트: failed
        db.table("ingestion_cursors").update({
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "uniprot").eq("query_hash", query_hash).execute()
        
        # 로그 실패
        db.table("ingestion_logs").update({
            "status": "failed",
            "error_message": str(e),
            "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
        }).eq("id", log_id).execute()
        
        raise


async def uniprot_enrich_from_catalog_job(ctx):
    """
    component_catalog의 target에서 UniProt 정보 자동 보강 Job
    
    properties.uniprot_id가 있는 target 컴포넌트를 찾아서
    UniProt에서 정보를 가져와 target_profiles에 저장합니다.
    """
    logger.info("uniprot_enrich_job_started")
    
    logger.info("uniprot_enrich_job_started")
    # 현재 Worker에서는 지원하지 않음 (Engine 의존성 제거)
    logger.warning("uniprot_enrich_job_not_implemented_in_worker")
    return {"status": "skipped", "message": "Not implemented in worker"}


async def uniprot_batch_sync_job(ctx, uniprot_ids: List[str]):
    """
    대량 UniProt ID 동기화 Job
    
    배치로 나누어 처리하여 API rate limit를 준수합니다.
    
    Args:
        ctx: Arq 컨텍스트
        uniprot_ids: 동기화할 UniProt ID 전체 목록
    """
    logger.info("uniprot_batch_sync_started", total=len(uniprot_ids))
    
    db = get_supabase()
    
    # 배치 크기
    BATCH_SIZE = 25
    
    total_stats = {"fetched": 0, "new": 0, "updated": 0, "errors": 0}
    
    import httpx
    import json
    import hashlib
    
    base_url = "https://rest.uniprot.org/uniprotkb/search"
    
    for i in range(0, len(uniprot_ids), BATCH_SIZE):
        batch = uniprot_ids[i:i + BATCH_SIZE]
        
        try:
            # 검색 쿼리 구성
            search_query = " OR ".join([f"accession:{uid}" for uid in batch])
            
            params = {
                "query": search_query,
                "format": "json",
                "fields": "accession,id,protein_name,gene_names,organism_name,cc_function,xref_chembl,xref_drugbank",
                "size": BATCH_SIZE
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(base_url, params=params)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                
                fetched_count = len(results)
                new_count = 0
                updated_count = 0
                
                for item in results:
                    primary_accession = item.get("primaryAccession")
                    
                    # 데이터 추출 (sync_job과 동일)
                    protein_desc = item.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "")
                    
                    genes = item.get("genes", [])
                    gene_symbol = genes[0].get("geneName", {}).get("value", "") if genes else None
                    
                    comments = item.get("comments", [])
                    function_summary = ""
                    for comment in comments:
                        if comment.get("commentType") == "FUNCTION":
                            function_summary = comment.get("texts", [])[0].get("value", "")
                            break
                    
                    organism = item.get("organism", {}).get("scientificName", "Homo sapiens")
                    
                    # External Refs
                    xrefs = {}
                    for ref in item.get("uniProtKBCrossReferences", []):
                        db_name = ref.get("database")
                        if db_name in ["ChEMBL", "DrugBank"]:
                            if db_name not in xrefs:
                                xrefs[db_name] = []
                            xrefs[db_name].append(ref.get("id"))
                    
                    # Raw Data 저장
                    payload = item
                    checksum = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                    
                    db.table("raw_source_records").upsert({
                        "source": "uniprot",
                        "external_id": primary_accession,
                        "payload": payload,
                        "checksum": checksum,
                        "fetched_at": datetime.utcnow().isoformat()
                    }, on_conflict="source,external_id").execute()
                    
                    # Target Profile 저장
                    target_data = {
                        "uniprot_id": primary_accession,
                        "gene_symbol": gene_symbol,
                        "protein_name": protein_desc[:500],
                        "function_summary": function_summary[:2000],
                        "organism": organism,
                        "external_refs": xrefs,
                        "checksum": checksum,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    existing = db.table("target_profiles").select("id").eq("uniprot_id", primary_accession).execute()
                    
                    if existing.data:
                        db.table("target_profiles").update(target_data).eq("uniprot_id", primary_accession).execute()
                        updated_count += 1
                    else:
                        db.table("target_profiles").insert(target_data).execute()
                        new_count += 1
                
                total_stats["fetched"] += fetched_count
                total_stats["new"] += new_count
                total_stats["updated"] += updated_count
            
        except Exception as e:
            logger.warning("batch_failed", batch_start=i, error=str(e))
            total_stats["errors"] += len(batch)
        
        # 배치 간 딜레이
        await asyncio.sleep(1)
    
    logger.info("uniprot_batch_sync_completed", stats=total_stats)
    
    return {"status": "completed", "stats": total_stats}
