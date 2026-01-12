"""
Phase B Worker Jobs
Open Targets, HPA, ChEMBL, PubChem 동기화 Jobs
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


# ============================================================
# Open Targets Jobs
# ============================================================

async def opentargets_fetch_job(ctx, seed: Dict[str, Any]):
    """
    Open Targets Target-Disease 연관 동기화 Job
    
    Args:
        ctx: Arq 컨텍스트
        seed: {"ensembl_ids": [...]} or {"target_id": "..."}
    """
    logger.info("opentargets_fetch_job_started", seed=seed)
    
    db = get_supabase()
    start_time = datetime.utcnow()
    
    # 로그 생성을 가장 먼저 수행
    log_id = db.table("ingestion_logs").insert({
        "source": "opentargets",
        "phase": "sync",
        "status": "started",
        "meta": {"seed": seed}
    }).execute().data[0]["id"]
    
    # 커서 해시 생성 (inline)
    import hashlib
    ensembl_ids = seed.get("ensembl_ids", [])
    target_id = seed.get("target_id")
    query = seed.get("query")
    
    if target_id and target_id not in ensembl_ids:
        ensembl_ids.append(target_id)
    if query and query not in ensembl_ids:
        # 쿼리가 입력되면 Ensembl ID로 간주하고 추가
        ensembl_ids.append(query)
        
    # 기본 쿼리 설정
    if not ensembl_ids:
        # Ensembl ID가 없으면 기본 ADC 타겟 목록 사용
        logger.info("opentargets_using_default_targets")
        
        # HER2(ERBB2), TROP2(TACSTD2), CD20(MS4A1), CD19, TP53
        default_targets = [
            "ENSG00000141736", # ERBB2
            "ENSG00000184292", # TACSTD2
            "ENSG00000156738", # MS4A1
            "ENSG00000174059", # CD19
            "ENSG00000141510"  # TP53
        ]
        ensembl_ids.extend(default_targets)
        
        # 로그 업데이트: 기본 타겟 사용 알림
        db.table("ingestion_logs").update({
            "meta": {"seed": seed, "note": "Using default ADC targets"}
        }).eq("id", log_id).execute()

    query_key = ",".join(ensembl_ids[:5])
    query_hash = hashlib.md5(f"opentargets:{query_key}:{str(seed)}".encode()).hexdigest()[:16]
    
    # 커서 상태: running
    db.table("ingestion_cursors").upsert({
        "source": "opentargets",
        "query_hash": query_hash,
        "status": "running",
        "config": seed,
        "updated_at": datetime.utcnow().isoformat()
    }, on_conflict="source,query_hash").execute()
    
    try:
        # Open Targets GraphQL API 호출 (inline)
        import httpx
        import json
        
        base_url = "https://api.platform.opentargets.org/api/v4/graphql"
        
        fetched_count = 0
        updated_count = 0
        
        async with httpx.AsyncClient(timeout=60) as client:
            for ensembl_id in ensembl_ids:
                # GraphQL Query
                query = """
                query TargetAssociations($ensemblId: String!) {
                  target(ensemblId: $ensemblId) {
                    id
                    approvedSymbol
                    associatedDiseases {
                      rows {
                        disease {
                          id
                          name
                        }
                        score
                        datatypeScores {
                          id
                          score
                        }
                      }
                    }
                  }
                }
                """
                
                variables = {"ensemblId": ensembl_id}
                
                resp = await client.post(base_url, json={"query": query, "variables": variables})
                resp.raise_for_status()
                data = resp.json()
                
                target_data = data.get("data", {}).get("target")
                
                if target_data:
                    fetched_count += 1
                    
                    # 데이터 추출
                    associations = []
                    rows = target_data.get("associatedDiseases", {}).get("rows", [])
                    for row in rows:
                        associations.append({
                            "disease_id": row.get("disease", {}).get("id"),
                            "disease_name": row.get("disease", {}).get("name"),
                            "score": row.get("score"),
                            "datatype_scores": row.get("datatypeScores", [])
                        })
                    
                    # Raw Data 저장
                    payload = target_data
                    checksum = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                    
                    db.table("raw_source_records").upsert({
                        "source": "opentargets",
                        "external_id": ensembl_id,
                        "payload": payload,
                        "checksum": checksum,
                        "fetched_at": datetime.utcnow().isoformat()
                    }, on_conflict="source,external_id").execute()
                    
                    # Target Profile 업데이트 (associations)
                    # Ensembl ID로 매칭하거나, 없으면 Uniprot ID 매핑이 필요함.
                    # 여기서는 Ensembl ID가 있는 경우에만 업데이트
                    
                    existing = db.table("target_profiles").select("id").eq("ensembl_id", ensembl_id).execute()
                    
                    if existing.data:
                        db.table("target_profiles").update({
                            "associations": associations[:50], # 상위 50개만 저장 (JSON 크기 제한 고려)
                            "updated_at": datetime.utcnow().isoformat()
                        }).eq("ensembl_id", ensembl_id).execute()
                        updated_count += 1
                    else:
                        # Ensembl ID로 찾지 못했으면, gene_symbol로 시도 (fallback)
                        symbol = target_data.get("approvedSymbol")
                        if symbol:
                            existing_symbol = db.table("target_profiles").select("id").eq("gene_symbol", symbol).execute()
                            if existing_symbol.data:
                                db.table("target_profiles").update({
                                    "ensembl_id": ensembl_id, # Ensembl ID 업데이트
                                    "associations": associations[:50],
                                    "updated_at": datetime.utcnow().isoformat()
                                }).eq("gene_symbol", symbol).execute()
                                updated_count += 1
        
        stats = {"fetched": fetched_count, "new": 0, "updated": updated_count}
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        db.table("ingestion_cursors").update({
            "status": "idle",
            "last_success_at": datetime.utcnow().isoformat(),
            "stats": stats,
            "error_message": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "opentargets").eq("query_hash", query_hash).execute()
        
        db.table("ingestion_logs").update({
            "status": "completed",
            "duration_ms": duration_ms,
            "records_fetched": stats.get("fetched", 0),
            "records_new": stats.get("new", 0),
            "records_updated": stats.get("updated", 0)
        }).eq("id", log_id).execute()
        
        logger.info("opentargets_fetch_job_completed", stats=stats)
        return {"status": "completed", "stats": stats, "duration_ms": duration_ms}
        
    except Exception as e:
        logger.error("opentargets_fetch_job_failed", error=str(e))
        
        db.table("ingestion_cursors").update({
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "opentargets").eq("query_hash", query_hash).execute()
        
        db.table("ingestion_logs").update({
            "status": "failed",
            "error_message": str(e),
            "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
        }).eq("id", log_id).execute()
        
        raise


# ============================================================
# HPA Jobs
# ============================================================

async def hpa_fetch_job(ctx, seed: Dict[str, Any]):
    """
    HPA 발현 데이터 동기화 Job
    
    Args:
        ctx: Arq 컨텍스트
        seed: {"ensembl_ids": [...]} or {"gene_symbols": [...]}
    """
    logger.info("hpa_fetch_job_started", seed=seed)
    
    db = get_supabase()
    start_time = datetime.utcnow()
    
    # 커서 해시 생성 (inline)
    import hashlib
    query_hash = hashlib.md5(f"hpa:{str(seed)}".encode()).hexdigest()[:16]
    
    db.table("ingestion_cursors").upsert({
        "source": "hpa",
        "query_hash": query_hash,
        "status": "running",
        "config": seed,
        "updated_at": datetime.utcnow().isoformat()
    }, on_conflict="source,query_hash").execute()
    
    log_id = db.table("ingestion_logs").insert({
        "source": "hpa",
        "phase": "sync",
        "status": "started",
        "meta": {"seed": seed}
    }).execute().data[0]["id"]
    
    try:
        # HPA API 호출 (inline)
        import httpx
        import json
        
        base_url = "https://www.proteinatlas.org"
        
        # 기본 쿼리 설정
        if not seed.get("ensembl_ids") and not seed.get("gene_symbols"):
            logger.info("hpa_using_default_targets")
            # HER2(ERBB2), TROP2(TACSTD2), CD20(MS4A1), CD19, TP53
            seed["gene_symbols"] = ["ERBB2", "TACSTD2", "MS4A1", "CD19", "TP53"]
            
            db.table("ingestion_logs").update({
                "meta": {"seed": seed, "note": "Using default HPA targets"}
            }).eq("id", log_id).execute()

        identifiers = []
        identifiers.extend(seed.get("ensembl_ids", []))
        identifiers.extend(seed.get("gene_symbols", []))
        
        fetched_count = 0
        updated_count = 0
        
        async with httpx.AsyncClient(timeout=60) as client:
            for identifier in identifiers:
                url = f"{base_url}/{identifier}.json"
                
                try:
                    resp = await client.get(url)
                    if resp.status_code == 404:
                        logger.warning("hpa_not_found", identifier=identifier)
                        continue
                    resp.raise_for_status()
                    
                    data = resp.json()
                    fetched_count += 1
                    
                    # 데이터 정규화 및 추출
                    gene = data.get("Gene", "")
                    ensembl = data.get("Ensembl", "")
                    
                    if not gene and not ensembl:
                        continue
                        
                    # Tissue expression
                    tissue_expression = {}
                    for tissue in data.get("Tissue expression", []):
                        tissue_name = tissue.get("Tissue", "")
                        if tissue_name:
                            tissue_expression[tissue_name] = {
                                "level": tissue.get("Level", ""),
                                "reliability": tissue.get("Reliability", ""),
                            }
                            
                    # RNA specificity
                    rna_specificity = data.get("RNA tissue specificity", "")
                    
                    # Subcellular location
                    subcellular = []
                    for loc in data.get("Subcellular location", []):
                        if isinstance(loc, dict):
                            subcellular.append(loc.get("Location", ""))
                        else:
                            subcellular.append(str(loc))
                            
                    # Blood expression
                    blood_expression = {}
                    for item in data.get("Blood expression", []):
                        if isinstance(item, dict):
                            cell_type = item.get("Cell type", "")
                            if cell_type:
                                blood_expression[cell_type] = {
                                    "level": item.get("Level", ""),
                                    "tpm": item.get("TPM", 0)
                                }
                                
                    # Cancer expression
                    cancer_expression = {}
                    for cancer in data.get("Pathology", []):
                        if isinstance(cancer, dict):
                            cancer_name = cancer.get("Cancer", "")
                            if cancer_name:
                                cancer_expression[cancer_name] = {
                                    "high": cancer.get("High", 0),
                                    "medium": cancer.get("Medium", 0),
                                    "low": cancer.get("Low", 0),
                                    "not_detected": cancer.get("Not detected", 0)
                                }
                                
                    # Raw Data 저장
                    payload = data
                    checksum = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                    
                    db.table("raw_source_records").upsert({
                        "source": "hpa",
                        "external_id": ensembl or gene,
                        "payload": payload,
                        "checksum": checksum,
                        "fetched_at": datetime.utcnow().isoformat()
                    }, on_conflict="source,external_id").execute()
                    
                    # Target Profile 업데이트 (expression)
                    expression_data = {
                        "hpa": {
                            "tissue_expression": tissue_expression,
                            "rna_specificity": rna_specificity,
                            "subcellular_location": subcellular,
                            "blood_expression": blood_expression,
                            "cancer_expression": cancer_expression,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                    
                    # 기존 프로필 찾기
                    existing = None
                    if ensembl:
                        existing = db.table("target_profiles").select("id, expression").eq("ensembl_id", ensembl).execute()
                    
                    if not existing or not existing.data:
                        if gene:
                            existing = db.table("target_profiles").select("id, expression").eq("gene_symbol", gene).execute()
                            
                    if existing and existing.data:
                        current_expr = existing.data[0].get("expression", {}) or {}
                        current_expr.update(expression_data)
                        
                        db.table("target_profiles").update({
                            "expression": current_expr,
                            "updated_at": datetime.utcnow().isoformat()
                        }).eq("id", existing.data[0]["id"]).execute()
                        updated_count += 1
                    else:
                        # 새 프로필 생성 (gene_symbol이 있는 경우만)
                        if gene:
                            db.table("target_profiles").insert({
                                "gene_symbol": gene,
                                "ensembl_id": ensembl,
                                "protein_name": data.get("Protein name", ""),
                                "expression": expression_data,
                                "created_at": datetime.utcnow().isoformat()
                            }).execute()
                            updated_count += 1
                            
                except Exception as e:
                    logger.warning("hpa_fetch_failed", identifier=identifier, error=str(e))
        
        stats = {"fetched": fetched_count, "new": 0, "updated": updated_count}
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        db.table("ingestion_cursors").update({
            "status": "idle",
            "last_success_at": datetime.utcnow().isoformat(),
            "stats": stats,
            "error_message": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "hpa").eq("query_hash", query_hash).execute()
        
        db.table("ingestion_logs").update({
            "status": "completed",
            "duration_ms": duration_ms,
            "records_fetched": stats.get("fetched", 0),
            "records_new": stats.get("new", 0),
            "records_updated": stats.get("updated", 0)
        }).eq("id", log_id).execute()
        
        logger.info("hpa_fetch_job_completed", stats=stats)
        return {"status": "completed", "stats": stats, "duration_ms": duration_ms}
        
    except Exception as e:
        logger.error("hpa_fetch_job_failed", error=str(e))
        
        db.table("ingestion_cursors").update({
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "hpa").eq("query_hash", query_hash).execute()
        
        db.table("ingestion_logs").update({
            "status": "failed",
            "error_message": str(e),
            "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
        }).eq("id", log_id).execute()
        
        raise


# ============================================================
# ChEMBL Jobs
# ============================================================

async def chembl_fetch_job(ctx, seed: Dict[str, Any]):
    """
    ChEMBL 화합물/활성 동기화 Job
    
    Args:
        ctx: Arq 컨텍스트
        seed: {"chembl_ids": [...]} or {"smiles": "..."} or {"search": "..."}
    """
    logger.info("chembl_fetch_job_started", seed=seed)
    
    db = get_supabase()
    start_time = datetime.utcnow()
    
    # 로그 생성을 가장 먼저 수행
    log_id = db.table("ingestion_logs").insert({
        "source": "chembl",
        "phase": "sync",
        "status": "started",
        "meta": {"seed": seed}
    }).execute().data[0]["id"]
    
    # 커서 해시 생성 (inline)
    import hashlib
    
    # Batch Mode: Catalog에서 ID 조회
    if seed.get("batch_mode"):
        logger.info("chembl_batch_mode_enabled")
        # Fetch payloads/linkers with chembl_id
        compounds = db.table("component_catalog").select("chembl_id").in_("type", ["payload", "linker"]).not_.is_("chembl_id", "null").execute()
        catalog_ids = [c["chembl_id"] for c in compounds.data if c.get("chembl_id")]
        if catalog_ids:
            if not seed.get("chembl_ids"):
                seed["chembl_ids"] = []
            seed["chembl_ids"].extend(catalog_ids)
            logger.info("chembl_batch_compounds_loaded", count=len(catalog_ids))
        else:
            logger.warning("chembl_batch_no_compounds_found")
            # Linkers might fail to have ChEMBL IDs, which is expected.
            # We continue if there are other inputs, otherwise we might return early or let it run with default?
            # If batch mode is strictly for catalog items, we should probably return if no IDs found.
            if not seed.get("chembl_ids"):
                 return {"status": "completed", "message": "No compounds with ChEMBL ID found in Catalog"}
    
    # 기본 쿼리 설정
    if not seed.get("chembl_ids") and not seed.get("smiles") and not seed.get("search"):
        logger.info("chembl_using_default_targets")
        # T-DM1 (Trastuzumab emtansine)
        seed["chembl_ids"] = ["CHEMBL1201583"]
        
        db.table("ingestion_logs").update({
            "meta": {"seed": seed, "note": "Using default ChEMBL target"}
        }).eq("id", log_id).execute()

    query_hash = hashlib.md5(f"chembl:{str(seed)}".encode()).hexdigest()[:16]
    
    db.table("ingestion_cursors").upsert({
        "source": "chembl",
        "query_hash": query_hash,
        "status": "running",
        "config": seed,
        "updated_at": datetime.utcnow().isoformat()
    }, on_conflict="source,query_hash").execute()
    
    try:
        # ChEMBL API 호출 (inline)
        import httpx
        import json
        
        base_url = "https://www.ebi.ac.uk/chembl/api/data"
        
        chembl_ids = seed.get("chembl_ids", [])
        smiles = seed.get("smiles")
        search = seed.get("search")
        
        fetched_count = 0
        updated_count = 0
        
        async with httpx.AsyncClient(timeout=60) as client:
            # 1. ChEMBL ID로 조회
            for cid in chembl_ids:
                url = f"{base_url}/molecule/{cid}.json"
                try:
                    resp = await client.get(url)
                    if resp.status_code == 404:
                        logger.warning("chembl_not_found", chembl_id=cid)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    
                    # 활성 데이터 조회
                    act_url = f"{base_url}/activity.json"
                    act_resp = await client.get(act_url, params={"molecule_chembl_id": cid, "limit": 50})
                    activities = []
                    if act_resp.status_code == 200:
                        activities = act_resp.json().get("activities", [])
                    
                    data["activities_summary"] = activities
                    
                    # 저장 로직 호출
                    if await save_chembl_data(db, data):
                        updated_count += 1
                    fetched_count += 1
                    
                except Exception as e:
                    logger.warning("chembl_fetch_failed", chembl_id=cid, error=str(e))

            # 2. SMILES로 조회
            if smiles:
                url = f"{base_url}/molecule.json"
                try:
                    resp = await client.get(url, params={"molecule_structures__canonical_smiles__flexmatch": smiles, "limit": 5})
                    resp.raise_for_status()
                    molecules = resp.json().get("molecules", [])
                    
                    for mol in molecules:
                        cid = mol.get("molecule_chembl_id")
                        # 활성 데이터 조회
                        act_url = f"{base_url}/activity.json"
                        act_resp = await client.get(act_url, params={"molecule_chembl_id": cid, "limit": 50})
                        activities = []
                        if act_resp.status_code == 200:
                            activities = act_resp.json().get("activities", [])
                        mol["activities_summary"] = activities
                        
                        if await save_chembl_data(db, mol):
                            updated_count += 1
                        fetched_count += 1
                        
                except Exception as e:
                    logger.warning("chembl_smiles_failed", smiles=smiles, error=str(e))

            # 3. 텍스트 검색
            if search:
                url = f"{base_url}/molecule/search.json"
                try:
                    resp = await client.get(url, params={"q": search, "limit": 20})
                    resp.raise_for_status()
                    molecules = resp.json().get("molecules", [])
                    
                    for mol in molecules:
                        cid = mol.get("molecule_chembl_id")
                        # 활성 데이터 조회
                        act_url = f"{base_url}/activity.json"
                        act_resp = await client.get(act_url, params={"molecule_chembl_id": cid, "limit": 50})
                        activities = []
                        if act_resp.status_code == 200:
                            activities = act_resp.json().get("activities", [])
                        mol["activities_summary"] = activities
                        
                        if await save_chembl_data(db, mol):
                            updated_count += 1
                        fetched_count += 1
                        
                except Exception as e:
                    logger.warning("chembl_search_failed", search=search, error=str(e))
        
        stats = {"fetched": fetched_count, "new": 0, "updated": updated_count}
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        db.table("ingestion_cursors").update({
            "status": "idle",
            "last_success_at": datetime.utcnow().isoformat(),
            "stats": stats,
            "error_message": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "chembl").eq("query_hash", query_hash).execute()
        
        db.table("ingestion_logs").update({
            "status": "completed",
            "duration_ms": duration_ms,
            "records_fetched": stats.get("fetched", 0),
            "records_new": stats.get("new", 0),
            "records_updated": stats.get("updated", 0)
        }).eq("id", log_id).execute()
        
        logger.info("chembl_fetch_job_completed", stats=stats)
        return {"status": "completed", "stats": stats, "duration_ms": duration_ms}
        
    except Exception as e:
        logger.error("chembl_fetch_job_failed", error=str(e))
        
        db.table("ingestion_cursors").update({
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "chembl").eq("query_hash", query_hash).execute()
        
        db.table("ingestion_logs").update({
            "status": "failed",
            "error_message": str(e),
            "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
        }).eq("id", log_id).execute()
        
        raise

async def save_chembl_data(db, data):
    """ChEMBL 데이터 저장 헬퍼 함수"""
    import json
    import hashlib
    
    chembl_id = data.get("molecule_chembl_id")
    if not chembl_id:
        return False
        
    # Raw Data 저장
    payload = data
    checksum = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    
    db.table("raw_source_records").upsert({
        "source": "chembl",
        "external_id": chembl_id,
        "payload": payload,
        "checksum": checksum,
        "fetched_at": datetime.utcnow().isoformat()
    }, on_conflict="source,external_id").execute()
    
    # Compound Registry 저장
    structures = data.get("molecule_structures", {}) or {}
    properties = data.get("molecule_properties", {}) or {}
    
    compound_data = {
        "chembl_id": chembl_id,
        "canonical_smiles": structures.get("canonical_smiles"),
        "inchi_key": structures.get("standard_inchi_key"),
        "synonyms": [data.get("pref_name")] if data.get("pref_name") else [],
        "activities": data.get("activities_summary", []),
        "properties": {
            "mw_freebase": properties.get("mw_freebase"),
            "alogp": properties.get("alogp"),
            "hba": properties.get("hba"),
            "hbd": properties.get("hbd"),
            "psa": properties.get("psa"),
            "rtb": properties.get("rtb"),
            "ro3_pass": properties.get("ro3_pass"),
            "num_ro5_violations": properties.get("num_ro5_violations"),
            "cx_logp": properties.get("cx_logp"),
            "aromatic_rings": properties.get("aromatic_rings"),
            "heavy_atoms": properties.get("heavy_atoms"),
        },
        "checksum": checksum,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # 기존 항목 확인 (InChIKey 또는 ChEMBL ID)
    existing = None
    inchi_key = structures.get("standard_inchi_key")
    if inchi_key:
        existing = db.table("compound_registry").select("id").eq("inchi_key", inchi_key).execute()
    
    if not existing or not existing.data:
        existing = db.table("compound_registry").select("id").eq("chembl_id", chembl_id).execute()
        
    if existing and existing.data:
        db.table("compound_registry").update(compound_data).eq("id", existing.data[0]["id"]).execute()
        return True
    else:
        compound_data["created_at"] = datetime.utcnow().isoformat()
        db.table("compound_registry").insert(compound_data).execute()
        return True


# ============================================================
# PubChem Jobs
# ============================================================

async def pubchem_fetch_job(ctx, seed: Dict[str, Any]):
    """
    PubChem 화합물 동기화 Job
    
    Args:
        ctx: Arq 컨텍스트
        seed: {"cids": [...]} or {"inchi_keys": [...]} or {"names": [...]}
    """
    logger.info("pubchem_fetch_job_started", seed=seed)
    
    db = get_supabase()
    start_time = datetime.utcnow()
    
    # 로그 생성을 가장 먼저 수행
    log_id = db.table("ingestion_logs").insert({
        "source": "pubchem",
        "phase": "sync",
        "status": "started",
        "meta": {"seed": seed}
    }).execute().data[0]["id"]
    
    # 커서 해시 생성 (inline)
    import hashlib
    
    # Batch Mode: Catalog에서 ID 조회
    if seed.get("batch_mode"):
        logger.info("pubchem_batch_mode_enabled")
        # Fetch payloads/linkers with pubchem_cid or inchikey
        compounds = db.table("component_catalog").select("pubchem_cid, inchikey").in_("type", ["payload", "linker"]).or_("pubchem_cid.neq.null,inchikey.neq.null").execute()
        
        catalog_cids = [c["pubchem_cid"] for c in compounds.data if c.get("pubchem_cid")]
        catalog_inchis = [c["inchikey"] for c in compounds.data if c.get("inchikey") and not c.get("pubchem_cid")] # CID 우선
        
        if catalog_cids or catalog_inchis:
            if not seed.get("cids"):
                seed["cids"] = []
            if not seed.get("inchi_keys"):
                seed["inchi_keys"] = []
                
            seed["cids"].extend(catalog_cids)
            seed["inchi_keys"].extend(catalog_inchis)
            logger.info("pubchem_batch_compounds_loaded", cids=len(catalog_cids), inchis=len(catalog_inchis))
        else:
            logger.warning("pubchem_batch_no_compounds_found")
            if not seed.get("cids") and not seed.get("inchi_keys"):
                return {"status": "completed", "message": "No compounds with PubChem CID or InChIKey found in Catalog"}
    
    # 기본 쿼리 설정
    if not seed.get("cids") and not seed.get("inchi_keys") and not seed.get("names"):
        logger.info("pubchem_using_default_targets")
        # Aspirin (CID 2244)
        seed["cids"] = [2244]
        
        db.table("ingestion_logs").update({
            "meta": {"seed": seed, "note": "Using default PubChem target"}
        }).eq("id", log_id).execute()

    query_hash = hashlib.md5(f"pubchem:{str(seed)}".encode()).hexdigest()[:16]
    
    db.table("ingestion_cursors").upsert({
        "source": "pubchem",
        "query_hash": query_hash,
        "status": "running",
        "config": seed,
        "updated_at": datetime.utcnow().isoformat()
    }, on_conflict="source,query_hash").execute()
    
    try:
        # PubChem API 호출 (inline)
        import httpx
        import json
        import urllib.parse
        
        base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        
        cids = seed.get("cids", [])
        inchi_keys = seed.get("inchi_keys", [])
        smiles_list = seed.get("smiles", [])
        names = seed.get("names", [])
        
        fetched_count = 0
        updated_count = 0
        
        async with httpx.AsyncClient(timeout=60) as client:
            # 1. CIDs (Batch)
            for i in range(0, len(cids), 100):
                batch = cids[i:i+100]
                cid_str = ",".join(map(str, batch))
                url = f"{base_url}/compound/cid/{cid_str}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChI,InChIKey,IUPACName,XLogP,TPSA,Complexity,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,HeavyAtomCount/JSON"
                
                try:
                    resp = await client.get(url)
                    if resp.status_code == 404:
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    props = data.get("PropertyTable", {}).get("Properties", [])
                    
                    for prop in props:
                        if await save_pubchem_data(db, prop):
                            updated_count += 1
                        fetched_count += 1
                except Exception as e:
                    logger.warning("pubchem_cid_failed", batch=batch, error=str(e))

            # 2. InChIKey
            for key in inchi_keys:
                url = f"{base_url}/compound/inchikey/{key}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChI,InChIKey,IUPACName,XLogP,TPSA,Complexity,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,HeavyAtomCount/JSON"
                try:
                    resp = await client.get(url)
                    if resp.status_code == 404:
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    props = data.get("PropertyTable", {}).get("Properties", [])
                    for prop in props:
                        if await save_pubchem_data(db, prop):
                            updated_count += 1
                        fetched_count += 1
                except Exception as e:
                    logger.warning("pubchem_inchikey_failed", inchikey=key, error=str(e))

            # 3. SMILES
            if isinstance(smiles_list, str):
                smiles_list = [smiles_list]
            for smi in smiles_list:
                encoded_smi = urllib.parse.quote(smi, safe="")
                url = f"{base_url}/compound/smiles/{encoded_smi}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChI,InChIKey,IUPACName,XLogP,TPSA,Complexity,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,HeavyAtomCount/JSON"
                try:
                    resp = await client.get(url)
                    if resp.status_code == 404:
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    props = data.get("PropertyTable", {}).get("Properties", [])
                    for prop in props:
                        if await save_pubchem_data(db, prop):
                            updated_count += 1
                        fetched_count += 1
                except Exception as e:
                    logger.warning("pubchem_smiles_failed", smiles=smi, error=str(e))

            # 4. Names
            for name in names:
                encoded_name = urllib.parse.quote(name, safe="")
                url = f"{base_url}/compound/name/{encoded_name}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChI,InChIKey,IUPACName,XLogP,TPSA,Complexity,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,HeavyAtomCount/JSON"
                try:
                    resp = await client.get(url)
                    if resp.status_code == 404:
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    props = data.get("PropertyTable", {}).get("Properties", [])
                    
                    # Synonyms 조회
                    if props:
                        cid = props[0].get("CID")
                        syn_url = f"{base_url}/compound/cid/{cid}/synonyms/JSON"
                        syn_resp = await client.get(syn_url)
                        if syn_resp.status_code == 200:
                            syn_data = syn_resp.json()
                            info = syn_data.get("InformationList", {}).get("Information", [])
                            if info:
                                props[0]["Synonyms"] = info[0].get("Synonym", [])[:10]

                    for prop in props:
                        if await save_pubchem_data(db, prop):
                            updated_count += 1
                        fetched_count += 1
                except Exception as e:
                    logger.warning("pubchem_name_failed", name=name, error=str(e))
        
        stats = {"fetched": fetched_count, "new": 0, "updated": updated_count}
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        db.table("ingestion_cursors").update({
            "status": "idle",
            "last_success_at": datetime.utcnow().isoformat(),
            "stats": stats,
            "error_message": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "pubchem").eq("query_hash", query_hash).execute()
        
        db.table("ingestion_logs").update({
            "status": "completed",
            "duration_ms": duration_ms,
            "records_fetched": stats.get("fetched", 0),
            "records_new": stats.get("new", 0),
            "records_updated": stats.get("updated", 0)
        }).eq("id", log_id).execute()
        
        logger.info("pubchem_fetch_job_completed", stats=stats)
        return {"status": "completed", "stats": stats, "duration_ms": duration_ms}
        
    except Exception as e:
        logger.error("pubchem_fetch_job_failed", error=str(e))
        
        db.table("ingestion_cursors").update({
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("source", "pubchem").eq("query_hash", query_hash).execute()
        
        db.table("ingestion_logs").update({
            "status": "failed",
            "error_message": str(e),
            "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
        }).eq("id", log_id).execute()
        
        raise

async def save_pubchem_data(db, data):
    """PubChem 데이터 저장 헬퍼 함수"""
    import json
    import hashlib
    
    cid = data.get("CID")
    if not cid:
        return False
        
    # Raw Data 저장
    payload = data
    checksum = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    
    db.table("raw_source_records").upsert({
        "source": "pubchem",
        "external_id": str(cid),
        "payload": payload,
        "checksum": checksum,
        "fetched_at": datetime.utcnow().isoformat()
    }, on_conflict="source,external_id").execute()
    
    # Compound Registry 저장
    compound_data = {
        "pubchem_cid": str(cid),
        "canonical_smiles": data.get("CanonicalSMILES"),
        "inchi_key": data.get("InChIKey"),
        "synonyms": data.get("Synonyms", []),
        "properties": {
            "xlogp": data.get("XLogP"),
            "tpsa": data.get("TPSA"),
            "complexity": data.get("Complexity"),
            "hbd": data.get("HBondDonorCount"),
            "hba": data.get("HBondAcceptorCount"),
            "rotatable_bonds": data.get("RotatableBondCount"),
            "heavy_atoms": data.get("HeavyAtomCount"),
        },
        "checksum": checksum,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # 기존 항목 확인 (InChIKey 우선)
    existing = None
    inchi_key = data.get("InChIKey")
    if inchi_key:
        existing = db.table("compound_registry").select("id, checksum, pubchem_cid").eq("inchi_key", inchi_key).execute()
    
    if not existing or not existing.data:
        existing = db.table("compound_registry").select("id, checksum, pubchem_cid").eq("pubchem_cid", str(cid)).execute()
        
    if existing and existing.data:
        # PubChem CID 병합
        if not existing.data[0].get("pubchem_cid"):
            compound_data["pubchem_cid"] = str(cid)
            
        db.table("compound_registry").update(compound_data).eq("id", existing.data[0]["id"]).execute()
        return True
    else:
        compound_data["created_at"] = datetime.utcnow().isoformat()
        db.table("compound_registry").insert(compound_data).execute()
        return True


# ============================================================
# Batch Enrichment Job
# ============================================================

async def enrich_targets_batch_job(ctx):
    """
    component_catalog의 모든 타겟에 대해 일괄 보강
    """
    logger.info("enrich_targets_batch_started")
    # 현재 Worker에서는 지원하지 않음 (Engine 의존성 제거)
    logger.warning("enrich_targets_batch_job_not_implemented_in_worker")
    return {"status": "skipped", "message": "Not implemented in worker"}
