"""
PubMed RAG 기반 Seed 생성 Job
벡터 DB(literature_chunks)를 검색하여 ADC 후보 물질(Seed Set)을 자동 생성합니다.
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import structlog
from supabase import create_client, Client
import os
from pathlib import Path
from dotenv import load_dotenv
import json

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

# --- Dictionaries & Patterns (Simple Rule-based Extraction) ---
# 실제 운영 시에는 DB나 별도 파일로 관리 권장
TARGET_DICTIONARY = {
    "her2": "HER2", "erbb2": "HER2",
    "trop2": "TROP2", "tacstd2": "TROP2",
    "nectin-4": "Nectin-4", "nectin4": "Nectin-4",
    "egfr": "EGFR",
    "cd19": "CD19", "cd22": "CD22", "cd30": "CD30", "cd33": "CD33", "cd79b": "CD79b",
    "bcma": "BCMA", "tnfrsf17": "BCMA",
    "folr1": "FOLR1",
    "tf": "TF", "tissue factor": "TF"
}

PAYLOAD_DICTIONARY = {
    "mmae": "MMAE", "monomethyl auristatin e": "MMAE",
    "mmaf": "MMAF",
    "dm1": "DM1", "mertansine": "DM1",
    "dm4": "DM4",
    "dxd": "DXd", "deruxtecan": "DXd",
    "sn-38": "SN-38", "sn38": "SN-38",
    "calicheamicin": "Calicheamicin",
    "pbd": "PBD",
    "duocarmycin": "Duocarmycin"
}

LINKER_DICTIONARY = {
    "vc": "Val-Cit", "valine-citrulline": "Val-Cit",
    "mc-vc-pab": "Val-Cit",
    "ggfg": "GGFG",
    "smcc": "SMCC",
    "hydrazone": "Hydrazone",
    "disulfide": "Disulfide",
    "spdb": "SPDB",
    "maleimide": "Maleimide"
}

ANTIBODY_PATTERNS = [
    "trastuzumab", "pertuzumab", "sacituzumab", "datopotamab", "enfortumab",
    "brentuximab", "polatuzumab", "gemtuzumab", "inotuzumab", "tisotumab",
    "mirvetuximab", "loncastuximab", "belantamab"
]

async def rag_seed_query_job(ctx, run_id: str, config: Dict[str, Any]):
    """
    RAG 기반 Seed 생성 메인 Job
    
    Args:
        ctx: Arq 컨텍스트
        run_id: connector_runs 테이블의 ID
        config: 실행 설정 (seed_query_set_id, target_count 등)
    """
    logger.info("rag_seed_job_started", run_id=run_id, config=config)
    
    db = get_supabase()
    start_time = datetime.utcnow()
    
    try:
        # 1. 설정 파싱
        seed_query_set_id = config.get("seed_query_set_id")
        seed_set_name = config.get("seed_set_name", "RAG_Generated_Set")
        base_version = config.get("seed_set_version", "v1")
        timestamp_suffix = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        seed_set_version = f"{base_version}-{timestamp_suffix}"
        
        target_count = config.get("target_count", 100)
        top_k = config.get("retrieval", {}).get("top_k_default", 50)
        min_similarity = config.get("retrieval", {}).get("min_similarity", 0.5) # 임계값
        
        # 2. Seed Set 생성 (Draft 상태)
        seed_set_data = {
            "name": seed_set_name,
            "version": seed_set_version,
            "status": "draft",
            "source": "rag",
            "seed_query_set_id": seed_query_set_id
        }
        res = db.table("seed_sets").insert(seed_set_data).execute()
        seed_set_id = res.data[0]["id"]
        logger.info("seed_set_created", seed_set_id=seed_set_id)
        
        # 3. 쿼리 가져오기 (없으면 기본 쿼리 사용)
        queries = []
        if seed_query_set_id:
            q_res = db.table("seed_queries").select("query_text").eq("seed_query_set_id", seed_query_set_id).execute()
            queries = [r["query_text"] for r in q_res.data]
        
        if not queries:
            # 기본 쿼리 (Fallback)
            queries = [
                "antibody-drug conjugate HER2",
                "antibody-drug conjugate TROP2",
                "antibody-drug conjugate linker payload",
                "ADC toxicity mechanism",
                "novel ADC payload"
            ]
            
        # 4. 벡터 검색 및 엔티티 추출
        import httpx
        openai_key = os.getenv("OPENAI_API_KEY")
        
        extracted_items = [] # list of dict
        seen_combinations = set()
        
        async with httpx.AsyncClient(timeout=60) as client:
            for query_text in queries:
                if len(extracted_items) >= target_count * 2: # 충분히 모이면 중단
                    break
                    
                logger.info("processing_query", query=query_text)
                
                # 4.1 쿼리 임베딩
                emb_resp = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {openai_key}"},
                    json={"model": "text-embedding-3-small", "input": query_text}
                )
                if emb_resp.status_code != 200:
                    logger.error("embedding_failed", status=emb_resp.status_code)
                    continue
                    
                query_embedding = emb_resp.json()["data"][0]["embedding"]
                
                # 4.2 벡터 검색 (RPC 호출 권장, 여기서는 직접 쿼리 시뮬레이션)
                # Supabase pgvector RPC가 있다고 가정: match_literature_chunks
                try:
                    rpc_params = {
                        "query_embedding": query_embedding,
                        "match_threshold": min_similarity,
                        "match_count": top_k
                    }
                    # match_literature_chunks 함수는 006_add_search_function.sql 등에서 정의되어야 함.
                    # 없으면 직접 구현하거나 가정. 여기서는 에러 방지를 위해 try-except
                    chunks = db.rpc("match_literature_chunks", rpc_params).execute().data
                except Exception as e:
                    logger.warning("vector_search_rpc_failed", error=str(e))
                    # Fallback: 그냥 최근 chunk 가져오기 (테스트용)
                    chunks = db.table("literature_chunks").select("id, content, document_id").limit(top_k).execute().data
                
                # 4.3 엔티티 추출 (Rule-based)
                for chunk in chunks:
                    text = chunk.get("content", "").lower()
                    chunk_id = chunk.get("id")
                    
                    # Extract Components
                    target = _extract_from_dict(text, TARGET_DICTIONARY)
                    payload = _extract_from_dict(text, PAYLOAD_DICTIONARY)
                    linker = _extract_from_dict(text, LINKER_DICTIONARY)
                    antibody = _extract_antibody(text, ANTIBODY_PATTERNS)
                    
                    # Drug Name (Antibody + Payload 조합 등)
                    drug_name = "Unknown"
                    if antibody and payload:
                        drug_name = f"{antibody}-{payload}"
                    elif antibody:
                        drug_name = antibody
                    
                    # 유효한 조합인가? (적어도 하나는 있어야 함)
                    if not (target or payload or linker or antibody):
                        continue
                        
                    # 조합 Key
                    combo_key = f"{target}|{antibody}|{linker}|{payload}|{drug_name}"
                    if combo_key in seen_combinations:
                        continue
                    
                    seen_combinations.add(combo_key)
                    
                    # 점수 계산
                    score = 0
                    if target: score += 20
                    if payload: score += 20
                    if linker: score += 20
                    if antibody: score += 10
                    
                    extracted_items.append({
                        "target": target,
                        "antibody": antibody,
                        "linker": linker,
                        "payload": payload,
                        "drug_name": drug_name,
                        "score": score,
                        "chunk_id": chunk_id,
                        "snippet": text[:200] # 근거용
                    })
        
        # 5. DB 저장 (Entity & Seed Set Items)
        saved_count = 0
        
        # 점수순 정렬
        extracted_items.sort(key=lambda x: x["score"], reverse=True)
        
        for item in extracted_items[:target_count]:
            # 5.1 엔티티 ID 확보 (Get or Create)
            target_id = _get_or_create_entity(db, "entity_targets", item["target"]) if item["target"] else None
            antibody_id = _get_or_create_entity(db, "entity_antibodies", item["antibody"]) if item["antibody"] else None
            linker_id = _get_or_create_entity(db, "entity_linkers", item["linker"]) if item["linker"] else None
            payload_id = _get_or_create_entity(db, "entity_payloads", item["payload"]) if item["payload"] else None
            drug_id = _get_or_create_entity(db, "entity_drugs", item["drug_name"]) if item["drug_name"] else None
            
            # 5.2 Seed Set Item 저장
            try:
                item_res = db.table("seed_set_items").insert({
                    "seed_set_id": seed_set_id,
                    "target_id": target_id,
                    "antibody_id": antibody_id,
                    "linker_id": linker_id,
                    "payload_id": payload_id,
                    "drug_id": drug_id,
                    "confidence_score": item["score"],
                    "evidence_count": 1
                }).execute()
                
                # 5.3 Evidence 저장
                if item_res.data:
                    # 각 엔티티별로 근거 연결 (여기서는 단순화하여 하나만 연결)
                    # 실제로는 chunk_id를 통해 원문(PMID)을 찾아야 함
                    # chunk -> document -> pmid
                    chunk_info = db.table("literature_chunks").select("document_id").eq("id", item["chunk_id"]).single().execute()
                    doc_info = db.table("literature_documents").select("pmid").eq("id", chunk_info.data["document_id"]).single().execute()
                    pmid = doc_info.data["pmid"]
                    
                    evidence_data = {
                        "entity_type": "seed_item", # 대표로 seed_item에 연결
                        "entity_id": item_res.data[0]["id"], # seed_set_item id를 사용하려면 entity_type을 맞춰야 함.
                                                             # 설계상 entity_type은 target/antibody 등임.
                                                             # 여기서는 편의상 seed_item 자체에 대한 근거로 저장하거나,
                                                             # 각 구성요소(target_id 등)에 대해 저장해야 함.
                        "source": "PubMed",
                        "ref_id": pmid,
                        "chunk_id": item["chunk_id"],
                        "snippet": item["snippet"]
                    }
                    # entity_evidence 테이블 스키마에 맞게 조정 필요.
                    # entity_id는 uuid이므로 seed_set_items의 id를 넣으려면 entity_type='seed_item'으로 약속.
                    
                    db.table("entity_evidence").insert(evidence_data).execute()
                    
                saved_count += 1
                
            except Exception as e:
                logger.warning("seed_item_insert_failed", error=str(e))
                continue

        # 6. 결과 요약
        summary = {
            "retrieval": {"queries": len(queries)},
            "extraction": {"total_extracted": len(extracted_items)},
            "seed_set": {"id": seed_set_id, "items_created": saved_count}
        }
        
        logger.info("rag_seed_job_completed", summary=summary)
        return summary

    except Exception as e:
        logger.error("rag_seed_job_failed", error=str(e))
        raise e

# --- Helper Functions ---

def _extract_from_dict(text: str, dictionary: Dict[str, str]) -> Optional[str]:
    for key, value in dictionary.items():
        if key in text:
            return value
    return None

def _extract_antibody(text: str, patterns: List[str]) -> Optional[str]:
    for pattern in patterns:
        if pattern in text:
            return pattern.capitalize()
    return None

def _get_or_create_entity(db, table_name, name):
    if not name: return None
    try:
        # Check exist
        res = db.table(table_name).select("id").eq("name", name).execute()
        if res.data:
            return res.data[0]["id"]
        # Create
        res = db.table(table_name).insert({"name": name}).execute()
        if res.data:
            return res.data[0]["id"]
    except Exception:
        # Race condition or error
        res = db.table(table_name).select("id").eq("name", name).execute()
        if res.data:
            return res.data[0]["id"]
    return None
