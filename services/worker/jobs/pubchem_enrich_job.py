"""
PubChem Enrich Job - SMILES 자동 조회 및 표준화
payload_exact_name 기반으로 PubChem에서 구조 획득

Usage:
    python -m services.worker.jobs.pubchem_enrich_job
"""

import os
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# PubChem API
PUBCHEM_REST_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def search_pubchem_by_name(name: str) -> dict | None:
    """PubChem에서 이름으로 CID 및 SMILES 검색"""
    if not name or name.strip() == '':
        return None
    
    try:
        # 1. Name to CID
        url = f"{PUBCHEM_REST_URL}/compound/name/{requests.utils.quote(name)}/cids/JSON"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        cids = data.get("IdentifierList", {}).get("CID", [])
        
        if not cids:
            return None
        
        cid = cids[0]  # 첫 번째 CID 사용
        
        # 2. CID to SMILES
        smiles_url = f"{PUBCHEM_REST_URL}/compound/cid/{cid}/property/CanonicalSMILES,InChIKey,MolecularWeight/JSON"
        smiles_response = requests.get(smiles_url, timeout=10)
        
        if smiles_response.status_code != 200:
            return {"cid": cid, "smiles": None, "error": "Failed to get SMILES"}
        
        props = smiles_response.json().get("PropertyTable", {}).get("Properties", [{}])[0]
        
        return {
            "cid": cid,
            "smiles": props.get("CanonicalSMILES"),
            "inchi_key": props.get("InChIKey"),
            "mw": props.get("MolecularWeight")
        }
        
    except Exception as e:
        return {"error": str(e)}


def add_to_review_queue(supabase, seed_item_id: str, queue_type: str, proposed_patch: dict, confidence: float = 0.5, evidence: list = None):
    """Review Queue에 제안 추가"""
    try:
        supabase.table("golden_review_queue").insert({
            "seed_item_id": seed_item_id,
            "queue_type": queue_type,
            "proposed_patch": proposed_patch,
            "evidence_refs": evidence or [],
            "confidence": confidence,
            "status": "pending"
        }).execute()
    except Exception as e:
        print(f"  ! Failed to add to review_queue: {e}")


def is_field_verified(verified_json: dict, field: str) -> bool:
    """필드가 verified 상태인지 확인"""
    if not verified_json or not isinstance(verified_json, dict):
        return False
    return verified_json.get(field, False)


def execute_pubchem_enrich_job(limit: int = 100, force_update: bool = False) -> dict:
    """
    Main job: golden_seed_items의 payload_exact_name으로 PubChem에서 SMILES 조회
    
    규칙:
    - verified 필드는 자동 업데이트 금지 (Review Queue로 제안)
    - Proxy가 아닌 항목만 처리
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"success": False, "error": "Missing Supabase credentials"}
    
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # 1. SMILES가 비어있고 Proxy가 아닌 항목 조회
    query = supabase.table("golden_seed_items") \
        .select("id, drug_name_canonical, payload_exact_name, payload_smiles_standardized, proxy_smiles_flag, field_verified") \
        .eq("proxy_smiles_flag", False) \
        .or_("payload_smiles_standardized.is.null,payload_smiles_standardized.eq.") \
        .limit(limit)
    
    result = query.execute()
    seeds = result.data or []
    
    print(f"[pubchem_enrich_job] Processing {len(seeds)} seeds without SMILES...")
    
    enriched_count = 0
    queued_count = 0
    failed_count = 0
    
    for seed in seeds:
        seed_id = seed["id"]
        drug_name = seed.get("drug_name_canonical", "Unknown")
        payload_name = seed.get("payload_exact_name", "")
        verified_json = seed.get("field_verified") or {}
        
        print(f"\n[{drug_name}] Payload: {payload_name}")
        
        if not payload_name:
            print("  ! No payload_exact_name, skipping")
            failed_count += 1
            continue
        
        # 2. PubChem 검색
        pubchem_result = search_pubchem_by_name(payload_name)
        
        if pubchem_result and pubchem_result.get("smiles"):
            smiles = pubchem_result["smiles"]
            cid = pubchem_result.get("cid")
            inchi_key = pubchem_result.get("inchi_key")
            
            # 3. Verified 필드 체크
            if is_field_verified(verified_json, "payload_smiles_standardized") and not force_update:
                # 자동 업데이트 금지 → Review Queue로 제안
                print(f"  → Verified field, adding to Review Queue")
                add_to_review_queue(
                    supabase, seed_id, "enrichment_update",
                    {
                        "payload_smiles_standardized": {
                            "old": seed.get("payload_smiles_standardized", ""),
                            "new": smiles,
                            "source": "pubchem",
                            "evidence": [{"type": "PubChemCID", "id": str(cid)}]
                        }
                    },
                    confidence=0.9,
                    evidence=[{"type": "PubChemCID", "id": str(cid)}]
                )
                queued_count += 1
            else:
                # 4. 직접 업데이트
                try:
                    update_data = {
                        "payload_smiles_standardized": smiles,
                        "payload_cid": str(cid) if cid else None,
                        "payload_inchi_key": inchi_key
                    }
                    supabase.table("golden_seed_items").update(update_data).eq("id", seed_id).execute()
                    print(f"  ✓ SMILES: {smiles[:50]}... (CID: {cid})")
                    enriched_count += 1
                except Exception as e:
                    print(f"  ✗ Update failed: {e}")
                    failed_count += 1
        else:
            # 5. 실패 시 Proxy 제안
            print(f"  → PubChem not found, suggesting Proxy")
            add_to_review_queue(
                supabase, seed_id, "proxy_suggestion",
                {
                    "proxy_smiles_flag": {
                        "old": False,
                        "new": True,
                        "source": "pubchem_enrich_job",
                        "evidence": [{"type": "note", "id": f"PubChem search failed for: {payload_name}"}]
                    },
                    "proxy_reference": {
                        "old": "",
                        "new": f"{payload_name} core",
                        "source": "auto",
                        "evidence": []
                    }
                },
                confidence=0.3
            )
            queued_count += 1
    
    return {
        "success": True,
        "processed": len(seeds),
        "enriched": enriched_count,
        "queued": queued_count,
        "failed": failed_count
    }


if __name__ == "__main__":
    result = execute_pubchem_enrich_job()
    print(f"\n=== Job Complete ===")
    print(f"Enriched: {result.get('enriched', 0)}")
    print(f"Queued: {result.get('queued', 0)}")
    print(f"Failed: {result.get('failed', 0)}")
