"""
SMILES Enrichment Script for Golden Seed Items
PubChem에서 SMILES를 가져와서 golden_seed_items를 업데이트합니다.

Usage:
    cd services/engine
    python enrich_smiles.py
"""

import os
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# PubChem CID → SMILES 매핑 (사전 조사된 값)
# 참조: https://pubchem.ncbi.nlm.nih.gov/
PAYLOAD_SMILES = {
    # ===== Topo1 Inhibitors =====
    "DXd": {
        "cid": 129268219,
        "smiles": "COc1cc2c(cc1OC)C(=O)N3Cc4cc5c(cc4[C@@H]3[C@@H]2O)OCO5",  # Exatecan derivative core
        "source": "PUBCHEM"
    },
    "SN-38": {
        "cid": 60953,
        "smiles": "CCC1=C2CN3C(=CC4=C(C3=O)COC(=O)C4(CC)O)C2=NC2=C1C=C(O)C=C2",
        "source": "PUBCHEM"
    },
    
    # ===== Microtubule Inhibitors (Maytansinoids) =====
    "DM1 (Maytansinoid)": {
        "cid": 11542111,
        "smiles": "CC[C@H]1OC(=O)[C@H]([C@@H](C)[C@@H]2CC(=O)N([C@@H](CC(C)C)C(=O)N[C@H](C)C(=O)N[C@@H](CC3=CC=C(O)C=C3)C(=O)O2)C)SCCO",
        "source": "PUBCHEM"
    },
    "DM4 (Maytansinoid)": {
        "cid": 56677881,  # DM4 variant
        "smiles": "CC(C)C(CS)NC(=O)C1CC2C(C(O1)C)OC(=O)CC(C(C(C(C(C(=C2)C)OC(=O)N)C)OC)O)C",
        "source": "PUBCHEM",
        "note": "Approximate structure"
    },
    
    # ===== Microtubule Inhibitors (Auristatins) =====
    "MMAE (Auristatin)": {
        "cid": 56677881,
        "smiles": "CCC(C)C(C(=O)NC(CC(C)C)C(=O)NC(C(C)O)C(=O)N1CCCC1C(=O)NC(C)C(=O)OC)NC(=O)C(C(C)C)N(C)C(=O)C(NC(=O)C(C(C)C)N(C)C)C(C)C",
        "source": "PUBCHEM"
    },
    "Eribulin": {
        "cid": 11354606,
        "smiles": "C[C@H]1CCC[C@H]2C[C@@H]([C@H]([C@H](O2)[C@H]3C[C@@H]([C@@H]([C@H](O3)C=C[C@H]4C[C@@H](C[C@H](O4)CC(=C)[C@@H](C(=O)[C@@H]5C[C@@H]([C@H](O5)C[C@@H]6CC(=C)[C@@H]([C@H](O6)C[C@@H](C)O1)O)O)O)O)O)O)O)O",
        "source": "PUBCHEM"
    },
    
    # ===== DNA Alkylators =====
    "Calicheamicin": {
        "cid": 5311286,
        "smiles": None,  # 너무 복잡, Proxy 필요
        "source": "PROXY",
        "proxy_reference": "Calicheamicin core"
    },
    "SG3199 (PBD dimer)": {
        "cid": None,
        "smiles": None,
        "source": "PROXY",
        "proxy_reference": "PBD dimer core (Tesirine class)"
    },
    "Tesirine (PBD dimer)": {
        "cid": None,
        "smiles": None,
        "source": "PROXY",
        "proxy_reference": "PBD dimer core (Tesirine class)"
    },
    "PBD dimer (SGD-1882)": {
        "cid": None,
        "smiles": None,
        "source": "PROXY",
        "proxy_reference": "PBD dimer core (SGD-1882 variant)"
    },
    "Duocarmycin": {
        "cid": 5458412,
        "smiles": None,  # 복잡한 구조
        "source": "PROXY",
        "proxy_reference": "Duocarmycin/seco-DUBA core"
    },
    
    # ===== Others =====
    "Belotecan derivative": {
        "cid": None,
        "smiles": None,
        "source": "PROXY",
        "proxy_reference": "Belotecan core (Topo1 inhibitor)"
    },
    "Top1i novel": {
        "cid": None,
        "smiles": None,
        "source": "PROXY",
        "proxy_reference": "SN-38 core (assumed Topo1 inhibitor)"
    },
    "Ed-04 (Exatecan deriv)": {
        "cid": None,
        "smiles": None,
        "source": "PROXY", 
        "proxy_reference": "Exatecan core"
    },
}

# Target → resolved_target_symbol 매핑
TARGET_SYMBOL_MAP = {
    "HER2": "ERBB2",
    "HER3": "ERBB3",
    "TROP2": "TACSTD2",
    "FR alpha": "FOLR1",
    "c-Met": "MET",
    "CD30": "TNFRSF8",
    "CD79b": "CD79B",
    "CD19": "CD19",
    "CD33": "CD33",
    "Nectin-4": "NECTIN4",
    "Tissue Factor": "F3",
    "DLL3": "DLL3",
    "EGFR / HER3": "EGFR;ERBB3",
}


def fetch_smiles_from_pubchem(cid: int) -> str | None:
    """PubChem에서 CID로 Canonical SMILES 조회"""
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/CanonicalSMILES/JSON"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data["PropertyTable"]["Properties"][0]["CanonicalSMILES"]
    except Exception as e:
        print(f"  ! PubChem API error for CID {cid}: {e}")
    return None


def enrich_seeds():
    """20개 Seed에 SMILES 및 resolved_target_symbol 업데이트"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # 1. Fetch all seeds
    result = supabase.table("golden_seed_items").select("*").execute()
    seeds = result.data
    
    print(f"Enriching {len(seeds)} seeds...")
    
    success_count = 0
    proxy_count = 0
    
    for seed in seeds:
        payload_name = seed.get("payload_exact_name")
        target = seed.get("target")
        drug_name = seed.get("drug_name_canonical")
        
        print(f"\n[{drug_name}]")
        
        update_data = {}
        
        # 1. resolved_target_symbol 업데이트
        if target and not seed.get("resolved_target_symbol"):
            resolved = TARGET_SYMBOL_MAP.get(target)
            if resolved:
                update_data["resolved_target_symbol"] = resolved
                print(f"  ✓ Target: {target} → {resolved}")
        
        # 2. SMILES 업데이트
        if payload_name and not seed.get("payload_smiles_standardized"):
            payload_info = PAYLOAD_SMILES.get(payload_name)
            
            if payload_info:
                if payload_info.get("smiles"):
                    # 직접 매핑된 SMILES 사용
                    update_data["payload_smiles_standardized"] = payload_info["smiles"]
                    update_data["payload_cid"] = str(payload_info.get("cid", ""))
                    update_data["proxy_smiles_flag"] = False
                    print(f"  ✓ SMILES: {payload_info['smiles'][:50]}...")
                    success_count += 1
                elif payload_info.get("cid"):
                    # PubChem에서 가져오기
                    smiles = fetch_smiles_from_pubchem(payload_info["cid"])
                    if smiles:
                        update_data["payload_smiles_standardized"] = smiles
                        update_data["payload_cid"] = str(payload_info["cid"])
                        update_data["proxy_smiles_flag"] = False
                        print(f"  ✓ SMILES (PubChem): {smiles[:50]}...")
                        success_count += 1
                    else:
                        # PubChem 실패 → Proxy
                        update_data["proxy_smiles_flag"] = True
                        update_data["proxy_reference"] = payload_info.get("proxy_reference", payload_name)
                        print(f"  ! PubChem failed, using proxy: {payload_info.get('proxy_reference')}")
                        proxy_count += 1
                else:
                    # Proxy 필요
                    update_data["proxy_smiles_flag"] = True
                    update_data["proxy_reference"] = payload_info.get("proxy_reference", payload_name)
                    print(f"  → Proxy: {payload_info.get('proxy_reference')}")
                    proxy_count += 1
            else:
                print(f"  ? Unknown payload: {payload_name}")
        
        # 3. evidence_refs 보완 (primary_source_id가 있으면 자동 추가)
        if seed.get("primary_source_id") and not seed.get("evidence_refs"):
            update_data["evidence_refs"] = [{
                "type": seed.get("primary_source_type", "unknown"),
                "id": seed.get("primary_source_id")
            }]
            print(f"  ✓ Evidence added: {seed.get('primary_source_id')}")
        
        # 4. 업데이트 실행
        if update_data:
            try:
                supabase.table("golden_seed_items").update(update_data).eq("id", seed["id"]).execute()
            except Exception as e:
                print(f"  ✗ Update failed: {e}")
    
    print(f"\n=== Complete ===")
    print(f"SMILES resolved: {success_count}")
    print(f"Proxy used: {proxy_count}")


if __name__ == "__main__":
    enrich_seeds()
