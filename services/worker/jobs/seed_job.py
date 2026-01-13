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
    {"name": "MMAE", "inchikey": "FBOQWJKAQSDJHD-UHFFFAOYSA-N", "pubchem_cid": "11542250", "smiles": "CC[C@H](C)[C@@H]([C@@H](CC(=O)N1CCC[C@H]1[C@@H]([C@@H](C)C(=O)N[C@H](C)[C@H](C2=CC=CC=C2)O)OC)OC)N(C)C(=O)[C@H](C(C)C)NC(=O)[C@H](C(C)C)NC"}, # Monomethyl auristatin E
    {"name": "MMAF", "inchikey": "XDTMQSROBMDMFD-UHFFFAOYSA-N", "pubchem_cid": "9853053", "smiles": "O=C([C@H](CC1=CC=CC=C1)NC([C@H](C)[C@H]([C@@H]2CCCN2C(C[C@@H](OC)C(N(C)C([C@@H](NC([C@H](C(C)C)NC)=O)C(C)C)=O)[C@@H](C)CC)=O)OC)=O)O"}, # Monomethyl auristatin F
    {"name": "DXd", "inchikey": "YGYAWVDWJNRERW-UHFFFAOYSA-N", "pubchem_cid": "137346536", "smiles": "O=C1[C@](O)(CC)C2=C(CO1)C(N3CC4=C5C6=C(CC[C@@H]5NC(CO)=O)C(C)=C(F)C=C6N=C4C3=C2)=O"}, # Deruxtecan payload
    {"name": "SN-38", "inchikey": "UFLHZZXDIJEZRE-UHFFFAOYSA-N", "pubchem_cid": "104842", "smiles": "CCC1=C2CN3C(=CC4=C(C3=O)COC(=O)[C@@]4(CC)O)C2=NC5=C1C=C(C=C5)O"},
    {"name": "DM1", "inchikey": "OVSQDLIZRRETGV-UHFFFAOYSA-N", "pubchem_cid": "5352062", "smiles": "C[C@@H]1[C@@H]2C[C@]([C@@H](/C=C\C=C(\CC3=CC(=C(C(=C3)OC)Cl)N(C(=O)C[C@H]([C@]4(C1O4)C)OC(=O)[C@H](C)N(C)C(=O)CCS)C)/C)OC)(NC(=O)O2)O"}, # Mertansine
    {"name": "PBD dimer", "inchikey": None, "pubchem_cid": None, "smiles": None}, # Generic PBD
]

GOLD_LINKERS = [
    {"name": "Val-Cit", "inchikey": None, "pubchem_cid": None, "linker_type": "cleavable", "trigger": "cathepsin-b"},
    {"name": "GGFG", "inchikey": None, "pubchem_cid": None, "linker_type": "cleavable", "trigger": "cathepsin-b"},
    {"name": "SMCC", "inchikey": "ISWJOCWSPKFRBO-UHFFFAOYSA-N", "pubchem_cid": "6364619", "linker_type": "non-cleavable", "trigger": "none"},
    {"name": "SPDB", "inchikey": None, "pubchem_cid": None, "linker_type": "cleavable", "trigger": "disulfide"},
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
                "canonical_name": item.get("canonical_name", item["name"]),
                "synonyms": item.get("synonyms", []),
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
                "canonical_name": item.get("canonical_name", item["name"]),
                "synonyms": item.get("synonyms", []),
                "properties": {"target": item["target"]},
                "is_gold": True,
                "is_active": True,
                "updated_at": datetime.utcnow().isoformat()
            }
            # Explicit check for partial index (workspace_id is null)
            existing = db.table("component_catalog").select("id").eq("type", "antibody").eq("name", item["name"]).is_("workspace_id", "null").execute()
            if existing.data:
                db.table("component_catalog").update(data).eq("id", existing.data[0]["id"]).execute()
            else:
                db.table("component_catalog").insert(data).execute()
            stats["antibodies"] += 1

        # 3. Linkers
        for item in GOLD_LINKERS:
            data = {
                "type": "linker",
                "name": item["name"],
                "canonical_name": item.get("canonical_name", item["name"]),
                "synonyms": item.get("synonyms", []),
                "linker_type": item.get("linker_type"),
                "trigger": item.get("trigger"),
                "inchikey": item["inchikey"],
                "pubchem_cid": item["pubchem_cid"],
                "is_gold": True,
                "is_active": True,
                "updated_at": datetime.utcnow().isoformat()
            }
            existing = db.table("component_catalog").select("id").eq("type", "linker").eq("name", item["name"]).is_("workspace_id", "null").execute()
            if existing.data:
                db.table("component_catalog").update(data).eq("id", existing.data[0]["id"]).execute()
            else:
                db.table("component_catalog").insert(data).execute()
            stats["linkers"] += 1

        # 4. Payloads
        for item in GOLD_PAYLOADS:
            data = {
                "type": "payload",
                "name": item["name"],
                "canonical_name": item.get("canonical_name", item["name"]),
                "synonyms": item.get("synonyms", []),
                "smiles": item.get("smiles"),
                "inchikey": item["inchikey"],
                "pubchem_cid": item["pubchem_cid"],
                "is_gold": True,
                "is_active": True,
                "updated_at": datetime.utcnow().isoformat()
            }
            existing = db.table("component_catalog").select("id").eq("type", "payload").eq("name", item["name"]).is_("workspace_id", "null").execute()
            if existing.data:
                db.table("component_catalog").update(data).eq("id", existing.data[0]["id"]).execute()
            else:
                db.table("component_catalog").insert(data).execute()
            stats["payloads"] += 1
            
    except Exception as e:
        logger.error("seed_fetch_job_failed", error=str(e))
        raise

    logger.info("seed_fetch_job_completed", stats=stats)
    return {"status": "completed", "stats": stats}
