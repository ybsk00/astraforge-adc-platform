import asyncio
from typing import Dict, Any, List
import structlog
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

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

def get_supabase() -> Client:
    """Supabase 클라이언트"""
    return create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    )

logger = structlog.get_logger()

# Gold Standard Data Definitions
GOLD_TARGETS = [
    {"name": "HER2", "gene_symbol": "ERBB2", "uniprot_accession": "P04626", "ensembl_gene_id": "ENSG00000141736"},
    {"name": "TROP2", "gene_symbol": "TACSTD2", "uniprot_accession": "P09758", "ensembl_gene_id": "ENSG00000184292"},
    {"name": "Nectin-4", "gene_symbol": "NECTIN4", "uniprot_accession": "Q96NY8", "ensembl_gene_id": "ENSG00000143217"},
    {"name": "EGFR", "gene_symbol": "EGFR", "uniprot_accession": "P00533", "ensembl_gene_id": "ENSG00000146648"},
    {"name": "CD19", "gene_symbol": "CD19", "uniprot_accession": "P15391", "ensembl_gene_id": "ENSG00000174059"},
    {"name": "CD20", "gene_symbol": "MS4A1", "uniprot_accession": "P11836", "ensembl_gene_id": "ENSG00000156738"},
    {"name": "CD22", "gene_symbol": "CD22", "uniprot_accession": "P20273", "ensembl_gene_id": "ENSG00000012124"},
    {"name": "BCMA", "gene_symbol": "TNFRSF17", "uniprot_accession": "Q02223", "ensembl_gene_id": "ENSG00000048462"},
]

GOLD_PAYLOADS = [
    {"name": "MMAE", "inchikey": "FBOQWJKAQSDJHD-UHFFFAOYSA-N", "pubchem_cid": "11542250"}, # Monomethyl auristatin E
    {"name": "MMAF", "inchikey": "XDTMQSROBMDMFD-UHFFFAOYSA-N", "pubchem_cid": "9853053"}, # Monomethyl auristatin F
    {"name": "DXd", "inchikey": "YGYAWVDWJNRERW-UHFFFAOYSA-N", "pubchem_cid": "137346536"}, # Deruxtecan payload
    {"name": "SN-38", "inchikey": "UFLHZZXDIJEZRE-UHFFFAOYSA-N", "pubchem_cid": "104842"},
    {"name": "DM1", "inchikey": "OVSQDLIZRRETGV-UHFFFAOYSA-N", "pubchem_cid": "5352062"}, # Mertansine
    {"name": "PBD dimer", "inchikey": None, "pubchem_cid": None}, # Generic PBD
]

GOLD_LINKERS = [
    {"name": "Val-Cit", "inchikey": None, "pubchem_cid": None},
    {"name": "GGFG", "inchikey": None, "pubchem_cid": None},
    {"name": "SMCC", "inchikey": "ISWJOCWSPKFRBO-UHFFFAOYSA-N", "pubchem_cid": "6364619"},
    {"name": "SPDB", "inchikey": None, "pubchem_cid": None},
]

GOLD_ANTIBODIES = [
    {"name": "Trastuzumab", "target": "HER2"},
    {"name": "Sacituzumab", "target": "TROP2"},
    {"name": "Enfortumab", "target": "Nectin-4"},
    {"name": "Brentuximab", "target": "CD30"},
]

async def seed_fetch_job(ctx, seed: Dict[str, Any] = None):
    """
    기초 데이터 시딩 Job
    
    1. 고정된 Seed Data (Target, Antibody, Linker, Payload)를 component_catalog에 적재
    2. targets_seed_200.json 파일이 있으면 추가 로드
    """
    logger.info("seed_fetch_job_started")
    db = get_supabase()
    
    stats = {"targets": 0, "antibodies": 0, "linkers": 0, "payloads": 0}
    
    try:
        # 1. Targets
        # 1-1. Hardcoded Targets
        targets = list(GOLD_TARGETS) # Copy list
        
        # 1-2. Load from JSON file (targets_seed_200.json)
        import json
        from pathlib import Path
        
        # services/worker/seeds/targets_seed_200.json
        # 현재 파일 위치: services/worker/jobs/seed_job.py
        # -> ../seeds/targets_seed_200.json
        json_path = Path(__file__).parent.parent / "seeds" / "targets_seed_200.json"
        
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    file_targets = json.load(f)
                    logger.info("seed_file_loaded", path=str(json_path), count=len(file_targets))
                    
                    # Merge logic: gene_symbol 기준으로 중복 제거 (파일 데이터 우선)
                    existing_symbols = {t["gene_symbol"] for t in targets if "gene_symbol" in t}
                    
                    for ft in file_targets:
                        if ft.get("gene_symbol") and ft["gene_symbol"] not in existing_symbols:
                            targets.append(ft)
                        elif ft.get("gene_symbol") and ft["gene_symbol"] in existing_symbols:
                            # 이미 존재하면 넘어감 (기존 GOLD_TARGETS 우선)
                            pass
                            
            except Exception as e:
                logger.error("seed_file_load_failed", error=str(e))
        else:
            logger.warning("seed_file_not_found", path=str(json_path))
        
        for item in targets:
            data = {
                "type": "target",
                "name": item["name"],
                "gene_symbol": item.get("gene_symbol"),
                "uniprot_accession": item.get("uniprot_accession"),
                "ensembl_gene_id": item.get("ensembl_gene_id"),
                "is_gold": item.get("quality_grade") == "gold" or item.get("is_gold", False),
                "quality_grade": item.get("quality_grade", "silver"),
                "is_active": True,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert logic: gene_symbol이 있으면 그것으로, 없으면 name으로
            if data.get("gene_symbol"):
                # Check existing by gene_symbol
                existing = db.table("component_catalog").select("id").eq("type", "target").eq("gene_symbol", data["gene_symbol"]).is_("workspace_id", "null").execute()
                if existing.data:
                    db.table("component_catalog").update(data).eq("id", existing.data[0]["id"]).execute()
                else:
                    db.table("component_catalog").insert(data).execute()
            else:
                # Check existing by name
                existing = db.table("component_catalog").select("id").eq("type", "target").eq("name", data["name"]).is_("workspace_id", "null").execute()
                if existing.data:
                    db.table("component_catalog").update(data).eq("id", existing.data[0]["id"]).execute()
                else:
                    db.table("component_catalog").insert(data).execute()
            stats["targets"] += 1

        # 2. Antibodies
        for item in GOLD_ANTIBODIES:
            data = {
                "type": "antibody",
                "name": item["name"],
                "properties": {"target": item["target"]},
                "is_gold": True,
                "is_active": True,
                "updated_at": datetime.utcnow().isoformat()
            }
            db.table("component_catalog").upsert(data, on_conflict="type,name").execute()
            stats["antibodies"] += 1

        # 3. Linkers
        for item in GOLD_LINKERS:
            data = {
                "type": "linker",
                "name": item["name"],
                "inchikey": item["inchikey"],
                "pubchem_cid": item["pubchem_cid"],
                "is_gold": True,
                "is_active": True,
                "updated_at": datetime.utcnow().isoformat()
            }
            db.table("component_catalog").upsert(data, on_conflict="type,name").execute()
            stats["linkers"] += 1

        # 4. Payloads
        for item in GOLD_PAYLOADS:
            data = {
                "type": "payload",
                "name": item["name"],
                "inchikey": item["inchikey"],
                "pubchem_cid": item["pubchem_cid"],
                "is_gold": True,
                "is_active": True,
                "updated_at": datetime.utcnow().isoformat()
            }
            db.table("component_catalog").upsert(data, on_conflict="type,name").execute()
            stats["payloads"] += 1
            
    except Exception as e:
        logger.error("seed_fetch_job_failed", error=str(e))
        raise

    logger.info("seed_fetch_job_completed", stats=stats)
    return {"status": "completed", "stats": stats}
