import asyncio
from typing import Dict, Any, List
import structlog
from datetime import datetime
from jobs.worker import get_supabase
import httpx
import urllib.parse

logger = structlog.get_logger()

async def resolve_fetch_job(ctx, seed: Dict[str, Any] = None):
    """
    Component Catalog의 ID를 외부 DB(UniProt, PubChem, ChEMBL)를 통해 식별(Resolve)하는 Job
    
    1. Targets: gene_symbol -> UniProt Accession
    2. Compounds (Payload/Linker): name -> PubChem CID/InChIKey -> ChEMBL ID
    """
    logger.info("resolve_job_started")
    db = get_supabase()
    
    stats = {
        "targets_resolved": 0,
        "compounds_resolved": 0,
        "errors": 0,
        "total_scanned": 0
    }
    
    try:
        # 1. Resolve Targets (UniProt)
        # uniprot_accession이 없는 Target 조회
        targets = db.table("component_catalog").select("*").eq("type", "target").is_("uniprot_accession", "null").execute()
        
        async with httpx.AsyncClient() as client:
            for item in targets.data:
                stats["total_scanned"] += 1
                gene = item.get("gene_symbol") or item.get("name")
                if not gene:
                    continue
                
                try:
                    # UniProt Search
                    url = f"https://rest.uniprot.org/uniprotkb/search?query=gene_exact:{gene} AND organism_id:9606&fields=accession,id,gene_names&size=1"
                    resp = await client.get(url, timeout=10.0)
                    resp.raise_for_status()
                    data = resp.json()
                    
                    if data["results"]:
                        accession = data["results"][0]["primaryAccession"]
                        
                        # Update Catalog
                        db.table("component_catalog").update({
                            "uniprot_accession": accession,
                            "updated_at": datetime.utcnow().isoformat()
                        }).eq("id", item["id"]).execute()
                        
                        stats["targets_resolved"] += 1
                        logger.info("target_resolved", name=item["name"], accession=accession)
                    else:
                        logger.warning("target_not_found_in_uniprot", name=item["name"])
                        
                except Exception as e:
                    logger.error("resolve_target_failed", name=item["name"], error=str(e))
                    stats["errors"] += 1
                
                await asyncio.sleep(0.2) # Rate limit

        # 2. Resolve Compounds (PubChem & ChEMBL)
        # inchikey 또는 pubchem_cid가 없는 Payload/Linker 조회
        compounds = db.table("component_catalog").select("*").in_("type", ["payload", "linker"]).is_("inchikey", "null").execute()
        
        async with httpx.AsyncClient() as client:
            for item in compounds.data:
                stats["total_scanned"] += 1
                name = item.get("name")
                if not name:
                    continue
                
                updates = {}
                
                try:
                    # PubChem Search (Name -> CID, InChIKey)
                    encoded_name = urllib.parse.quote(name)
                    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/property/InChIKey,CID/JSON"
                    resp = await client.get(url, timeout=10.0)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if "PropertyTable" in data and "Properties" in data["PropertyTable"]:
                            props = data["PropertyTable"]["Properties"][0]
                            updates["inchikey"] = props.get("InChIKey")
                            updates["pubchem_cid"] = str(props.get("CID"))
                            logger.info("pubchem_resolved", name=name, cid=updates["pubchem_cid"])
                    
                    # ChEMBL Search (Name -> ChEMBL ID) - Optional if PubChem fails or for enrichment
                    # If we have InChIKey from PubChem, use it for ChEMBL
                    # But for now, let's try name search on ChEMBL if ID is missing
                    if not item.get("chembl_id"):
                        chembl_url = f"https://www.ebi.ac.uk/chembl/api/data/molecule/search?q={encoded_name}&format=json"
                        resp = await client.get(chembl_url, timeout=10.0)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("molecules"):
                                # Best match? Just take the first one for now
                                updates["chembl_id"] = data["molecules"][0]["molecule_chembl_id"]
                                logger.info("chembl_resolved", name=name, chembl_id=updates["chembl_id"])

                    if updates:
                        updates["updated_at"] = datetime.utcnow().isoformat()
                        db.table("component_catalog").update(updates).eq("id", item["id"]).execute()
                        stats["compounds_resolved"] += 1
                        
                except Exception as e:
                    logger.error("resolve_compound_failed", name=name, error=str(e))
                    stats["errors"] += 1
                
                await asyncio.sleep(0.5) # Rate limit

    except Exception as e:
        logger.error("resolve_job_fatal_error", error=str(e))
        raise

    logger.info("resolve_job_completed", stats=stats)
    return stats
