import asyncio
from typing import Dict, Any, List
import structlog
from datetime import datetime
from .worker import get_supabase

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
    Gold Standard 데이터를 component_catalog에 시딩하는 Job
    """
    logger.info("seed_job_started")
    db = get_supabase()
    
    stats = {"targets": 0, "payloads": 0, "linkers": 0, "antibodies": 0, "errors": 0}
    
    # 1. Targets
    for item in GOLD_TARGETS:
        try:
            data = {
                "type": "target",
                "name": item["name"],
                "gene_symbol": item["gene_symbol"],
                "uniprot_accession": item["uniprot_accession"],
                "ensembl_gene_id": item["ensembl_gene_id"],
                "is_gold": True,
                "is_active": True,
                "quality_grade": "gold"
            }
            # Upsert based on type + name (using the unique index we created)
            # Note: Supabase-py upsert requires 'on_conflict' column
            # We created a unique index on (type, name) where workspace_id is null.
            # However, postgrest upsert might need explicit constraint name or columns.
            # Let's try upserting by 'type, name' if possible, or just insert and ignore conflict?
            # Better to check existence first or use upsert with on_conflict.
            
            # Since we can't easily specify partial index constraint in postgrest,
            # we will try to select first.
            existing = db.table("component_catalog").select("id").eq("type", "target").eq("name", item["name"]).is_("workspace_id", "null").execute()
            
            if existing.data:
                db.table("component_catalog").update(data).eq("id", existing.data[0]["id"]).execute()
            else:
                db.table("component_catalog").insert(data).execute()
            stats["targets"] += 1
        except Exception as e:
            logger.error("seed_target_failed", name=item["name"], error=str(e))
            stats["errors"] += 1

    # 2. Payloads
    for item in GOLD_PAYLOADS:
        try:
            data = {
                "type": "payload",
                "name": item["name"],
                "inchikey": item["inchikey"],
                "pubchem_cid": item["pubchem_cid"],
                "is_gold": True,
                "is_active": True,
                "quality_grade": "gold"
            }
            existing = db.table("component_catalog").select("id").eq("type", "payload").eq("name", item["name"]).is_("workspace_id", "null").execute()
            if existing.data:
                db.table("component_catalog").update(data).eq("id", existing.data[0]["id"]).execute()
            else:
                db.table("component_catalog").insert(data).execute()
            stats["payloads"] += 1
        except Exception as e:
            logger.error("seed_payload_failed", name=item["name"], error=str(e))
            stats["errors"] += 1

    # 3. Linkers
    for item in GOLD_LINKERS:
        try:
            data = {
                "type": "linker",
                "name": item["name"],
                "inchikey": item["inchikey"],
                "pubchem_cid": item["pubchem_cid"],
                "is_gold": True,
                "is_active": True,
                "quality_grade": "gold"
            }
            existing = db.table("component_catalog").select("id").eq("type", "linker").eq("name", item["name"]).is_("workspace_id", "null").execute()
            if existing.data:
                db.table("component_catalog").update(data).eq("id", existing.data[0]["id"]).execute()
            else:
                db.table("component_catalog").insert(data).execute()
            stats["linkers"] += 1
        except Exception as e:
            logger.error("seed_linker_failed", name=item["name"], error=str(e))
            stats["errors"] += 1

    # 4. Antibodies
    for item in GOLD_ANTIBODIES:
        try:
            data = {
                "type": "antibody",
                "name": item["name"],
                "properties": {"target": item["target"]},
                "is_gold": True,
                "is_active": True,
                "quality_grade": "gold"
            }
            existing = db.table("component_catalog").select("id").eq("type", "antibody").eq("name", item["name"]).is_("workspace_id", "null").execute()
            if existing.data:
                db.table("component_catalog").update(data).eq("id", existing.data[0]["id"]).execute()
            else:
                db.table("component_catalog").insert(data).execute()
            stats["antibodies"] += 1
        except Exception as e:
            logger.error("seed_antibody_failed", name=item["name"], error=str(e))
            stats["errors"] += 1

    logger.info("seed_job_completed", stats=stats)
    return stats
