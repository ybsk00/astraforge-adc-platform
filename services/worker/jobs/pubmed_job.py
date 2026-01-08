"""
PubMed Worker Jobs
문헌 수집, 청킹, 임베딩 Job 정의
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
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


async def pubmed_fetch_job(ctx, seed: Dict[str, Any], cursor: Optional[Dict] = None):
    """
    PubMed 문헌 수집 Job
    
    Args:
        ctx: Arq 컨텍스트
        seed: 시드 데이터 {"query": "...", "retmax": 100}
        cursor: 이전 커서 상태 (증분 수집용)
    
    Returns:
        실행 결과
    """
    logger.info("pubmed_fetch_job_started", seed=seed)
    
    db = get_supabase()
    start_time = datetime.utcnow()
    
    # 커서 ID 생성 (inline implementation instead of app.connectors)
    import hashlib
    # 기본 쿼리: ADC 관련 문헌 검색 (쿼리가 비어있으면 사용)
    query = seed.get("query", "") or "antibody drug conjugate OR ADC therapy OR targeted drug delivery"
    query_hash = hashlib.md5(f"pubmed:{query}:{str(seed)}".encode()).hexdigest()[:16]
    
    # 커서 상태 업데이트: running
    db.table("ingestion_cursors").upsert({
        "source": "pubmed",
        "query_hash": query_hash,
        "status": "running",
        "config": seed,
        "updated_at": datetime.utcnow().isoformat()
    }, on_conflict="source,query_hash").execute()
    
    # 로그 시작
    log_id = db.table("ingestion_logs").insert({
        "source": "pubmed",
        "phase": "fetch",
        "status": "started",
        "meta": {"seed": seed}
    }).execute().data[0]["id"]
    
    try:
        # PubMed E-utilities API 호출 (inline implementation)
        import httpx
        
        ncbi_api_key = os.getenv("NCBI_API_KEY", "")
        ncbi_email = os.getenv("NCBI_EMAIL", "")
        
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        retmax = seed.get("retmax", 10)
        
        async with httpx.AsyncClient(timeout=60) as client:
            # 1. ESearch: 검색하여 PMID 목록 얻기
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": retmax,
                "retmode": "json",
                "api_key": ncbi_api_key,
                "email": ncbi_email
            }
            
            search_resp = await client.get(f"{base_url}/esearch.fcgi", params=search_params)
            search_data = search_resp.json()
            
            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            
            if not pmids:
                logger.info("pubmed_no_results", query=query)
                stats = {"fetched": 0, "new": 0, "updated": 0}
            else:
                # 2. EFetch: PMID로 상세 정보 가져오기
                fetch_params = {
                    "db": "pubmed",
                    "id": ",".join(pmids),
                    "retmode": "xml",
                    "api_key": ncbi_api_key,
                    "email": ncbi_email
                }
                
                fetch_resp = await client.get(f"{base_url}/efetch.fcgi", params=fetch_params)
                
                # XML 파싱 (간단 버전: 정규식 사용)
                import re
                xml_content = fetch_resp.text
                
                # 논문 데이터 추출
                new_count = 0
                for pmid in pmids:
                    # 이미 존재하는지 확인 (pmid 컬럼 사용)
                    existing = db.table("literature_documents").select("id").eq("pmid", pmid).execute()
                    
                    if not existing.data:
                        # 제목 추출 (간단한 정규식)
                        title_match = re.search(rf'<PMID[^>]*>{pmid}</PMID>.*?<ArticleTitle>([^<]+)</ArticleTitle>', xml_content, re.DOTALL)
                        title = title_match.group(1) if title_match else f"PubMed Article {pmid}"
                        
                        # Abstract 추출
                        abstract_match = re.search(rf'<PMID[^>]*>{pmid}</PMID>.*?<AbstractText>([^<]+)</AbstractText>', xml_content, re.DOTALL)
                        abstract = abstract_match.group(1) if abstract_match else ""
                        
                        # raw_source_records에 저장 (schema에 맞춤)
                        import json
                        payload_data = {"pmid": pmid, "title": title, "abstract": abstract[:2000]}
                        checksum = hashlib.md5(json.dumps(payload_data, sort_keys=True).encode()).hexdigest()
                        
                        db.table("raw_source_records").insert({
                            "source": "pubmed",
                            "external_id": pmid,
                            "payload": payload_data,
                            "checksum": checksum
                        }).execute()
                        
                        # literature_documents에 저장 (schema에 맞춤)
                        db.table("literature_documents").insert({
                            "pmid": pmid,
                            "title": title[:500],
                            "abstract": abstract[:5000] if abstract else None,
                            "meta": {"source": "pubmed", "fetched_at": datetime.utcnow().isoformat()}
                        }).execute()
                        
                        new_count += 1
                
                stats = {"fetched": len(pmids), "new": new_count, "updated": 0}
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # 커서 상태 업데이트: idle
        db.table("ingestion_cursors").update({
            "status": "idle",
            "last_success_at": datetime.utcnow().isoformat(),
            "stats": stats,
            "error_message": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "pubmed").eq("query_hash", query_hash).execute()
        
        # 로그 완료
        db.table("ingestion_logs").update({
            "status": "completed",
            "duration_ms": duration_ms,
            "records_fetched": stats.get("fetched", 0),
            "records_new": stats.get("new", 0),
            "records_updated": stats.get("updated", 0)
        }).eq("id", log_id).execute()
        
        logger.info("pubmed_fetch_job_completed", stats=stats)
        
        # 새로 추가된 문헌에 대해 청킹 Job 예약
        if stats.get("new", 0) > 0:
            # 최근 추가된 문헌 조회
            new_docs = db.table("literature_documents").select("id").order(
                "created_at", desc=True
            ).limit(stats["new"]).execute()
            
            doc_ids = [d["id"] for d in new_docs.data]
            
            # 청킹 Job enqueue
            from arq import create_pool
            from arq.connections import RedisSettings
            
            pool = await create_pool(
                RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379"))
            )
            await pool.enqueue_job("pubmed_chunk_job", doc_ids)
            
            logger.info("chunk_job_enqueued", doc_count=len(doc_ids))
        
        return {"status": "completed", "stats": stats, "duration_ms": duration_ms}
        
    except Exception as e:
        logger.error("pubmed_fetch_job_failed", error=str(e))
        
        # 커서 상태 업데이트: failed
        db.table("ingestion_cursors").update({
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "pubmed").eq("query_hash", query_hash).execute()
        
        # 로그 실패
        db.table("ingestion_logs").update({
            "status": "failed",
            "error_message": str(e),
            "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
        }).eq("id", log_id).execute()
        
        raise


async def pubmed_chunk_job(ctx, doc_ids: list):
    """
    문헌 청킹 Job
    
    Args:
        ctx: Arq 컨텍스트
        doc_ids: 청킹할 문헌 ID 목록
    """
    logger.info("pubmed_chunk_job_started", doc_count=len(doc_ids))
    
    db = get_supabase()
    
    # 토큰 기반 청킹 (간단 버전: 문자 수 기반)
    CHUNK_SIZE = 1500  # 약 300-400 토큰
    OVERLAP = 200
    
    chunk_ids = []
    
    for doc_id in doc_ids:
        try:
            # 문헌 조회
            doc = db.table("literature_documents").select(
                "id, title, abstract"
            ).eq("id", doc_id).execute()
            
            if not doc.data:
                continue
            
            doc_data = doc.data[0]
            
            # 텍스트 준비
            title = doc_data.get("title", "")
            abstract = doc_data.get("abstract", "")
            content = f"{title}\n\n{abstract}"
            
            if not content.strip():
                continue
            
            # 청킹
            chunks = []
            start = 0
            chunk_idx = 0
            
            while start < len(content):
                end = min(start + CHUNK_SIZE, len(content))
                chunk_text = content[start:end]
                
                if chunk_text.strip():
                    chunks.append({
                        "document_id": doc_id,
                        "chunk_index": chunk_idx,
                        "content": chunk_text.strip(),
                        "token_count": len(chunk_text) // 4,  # 대략적 추정
                        "embedding_status": "pending"
                    })
                    chunk_idx += 1
                
                start = end - OVERLAP if end < len(content) else end
            
            # 청크 저장 (기존 삭제 후 재생성)
            db.table("literature_chunks").delete().eq("document_id", doc_id).execute()
            
            if chunks:
                result = db.table("literature_chunks").insert(chunks).execute()
                chunk_ids.extend([c["id"] for c in result.data])
            
        except Exception as e:
            logger.warning("chunk_failed", doc_id=doc_id, error=str(e))
    
    logger.info("pubmed_chunk_job_completed", chunks_created=len(chunk_ids))
    
    # 임베딩 Job enqueue
    if chunk_ids:
        from arq import create_pool
        from arq.connections import RedisSettings
        
        pool = await create_pool(
            RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379"))
        )
        
        # 배치로 나누어 enqueue
        BATCH_SIZE = 50
        for i in range(0, len(chunk_ids), BATCH_SIZE):
            batch = chunk_ids[i:i + BATCH_SIZE]
            await pool.enqueue_job("pubmed_embed_job", batch)
        
        logger.info("embed_jobs_enqueued", total_chunks=len(chunk_ids))
    
    return {"chunks_created": len(chunk_ids)}


async def pubmed_embed_job(ctx, chunk_ids: list):
    """
    청크 임베딩 생성 Job
    
    Args:
        ctx: Arq 컨텍스트
        chunk_ids: 임베딩할 청크 ID 목록
    """
    logger.info("pubmed_embed_job_started", chunk_count=len(chunk_ids))
    
    db = get_supabase()
    
    # OpenAI API Key 확인
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.warning("openai_key_missing", message="Skipping embedding")
        return {"status": "skipped", "reason": "OPENAI_API_KEY not set"}
    
    import httpx
    
    embedded_count = 0
    
    for chunk_id in chunk_ids:
        try:
            # 청크 조회
            chunk = db.table("literature_chunks").select(
                "id, content, embedding_status"
            ).eq("id", chunk_id).execute()
            
            if not chunk.data:
                continue
            
            chunk_data = chunk.data[0]
            
            if chunk_data.get("embedding_status") == "completed":
                continue
            
            content = chunk_data["content"]
            
            # OpenAI Embedding API 호출
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "text-embedding-3-small",
                        "input": content[:8000]  # 토큰 제한
                    }
                )
                
                if response.status_code != 200:
                    logger.warning("embedding_api_failed", 
                                  chunk_id=chunk_id, 
                                  status=response.status_code)
                    continue
                
                result = response.json()
                embedding = result["data"][0]["embedding"]
            
            # 임베딩 저장
            db.table("literature_chunks").update({
                "embedding": embedding,
                "embedding_status": "completed"
            }).eq("id", chunk_id).execute()
            
            embedded_count += 1
            
            # Rate limit 고려 (3000 RPM)
            await asyncio.sleep(0.02)
            
        except Exception as e:
            logger.warning("embed_failed", chunk_id=chunk_id, error=str(e))
            
            db.table("literature_chunks").update({
                "embedding_status": "failed"
            }).eq("id", chunk_id).execute()
    
    logger.info("pubmed_embed_job_completed", embedded=embedded_count)
    
    return {"embedded": embedded_count, "total": len(chunk_ids)}
