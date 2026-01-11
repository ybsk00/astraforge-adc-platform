"""
Seed Golden Set Data v3
임상 단계 유망 후보 물질 데이터 확충 (10종 이상)
"""
import asyncio
import uuid
from typing import List, Dict, Any

# 임상 데이터 정의
CLINICAL_DATA = [
    {"name": "DS-1062 (Dato-DXd)", "target": "TROP-2", "antibody": "Datopotamab", "linker": "GGFG", "payload": "DXd", "dar": 4.0, "status": "Phase 3", "ic50": 0.2},
    {"name": "U3-1402 (Patritumab Deruxtecan)", "target": "HER3", "antibody": "Patritumab", "linker": "GGFG", "payload": "DXd", "dar": 8.0, "status": "Phase 3", "ic50": 0.15},
    {"name": "ARX788", "target": "HER2", "antibody": "Trastuzumab", "linker": "AS269", "payload": "Amberstatin", "dar": 1.9, "status": "Phase 3", "ic50": 0.05},
    {"name": "MRG003", "target": "EGFR", "antibody": "Anti-EGFR", "linker": "Val-Cit", "payload": "MMAE", "dar": 3.8, "status": "Phase 2", "ic50": 0.9},
    {"name": "PF-06804103", "target": "HER2", "antibody": "Anti-HER2", "linker": "Val-Cit", "payload": "Auristatin", "dar": 4.0, "status": "Phase 1", "ic50": 0.6},
    {"name": "XMT-1536", "target": "NaPi2b", "antibody": "Anti-NaPi2b", "linker": "Dolaflexin", "payload": "Auristatin", "dar": 10.0, "status": "Phase 1", "ic50": 0.1},
    {"name": "STRO-002", "target": "FolRα", "antibody": "Anti-FolRα", "linker": "SC209", "payload": "Maytansinoid", "dar": 4.0, "status": "Phase 1", "ic50": 0.3},
    {"name": "SGN-B6A", "target": "Integrin β6", "antibody": "Anti-β6", "linker": "Val-Cit", "payload": "MMAE", "dar": 4.0, "status": "Phase 1", "ic50": 1.1},
    {"name": "ABBV-154", "target": "TNFα", "antibody": "Adalimumab", "linker": "Val-Cit", "payload": "Glucocorticoid", "dar": 2.0, "status": "Phase 2", "ic50": 5.0},
    {"name": "TR1801-ADC", "target": "c-Met", "antibody": "Anti-cMet", "linker": "Val-Cit", "payload": "PBD", "dar": 2.0, "status": "Phase 1", "ic50": 0.02}
]

async def seed_v3(db):
    print(f"Seeding {len(CLINICAL_DATA)} clinical candidates...")
    
    # 1. Insert Candidates
    cand_inserts = []
    for d in CLINICAL_DATA:
        cand_inserts.append({
            "id": str(uuid.uuid4()),
            "drug_name": d["name"],
            "target": d["target"],
            "antibody": d["antibody"],
            "linker": d["linker"],
            "payload": d["payload"],
            "dar_nominal": d["dar"],
            "approval_status": d["status"]
        })
    
    res = await db.table("golden_candidates").insert(cand_inserts).execute()
    inserted_cands = {c["drug_name"]: c["id"] for c in res.data}
    
    # 2. Insert Measurements
    meas_inserts = []
    for d in CLINICAL_DATA:
        cid = inserted_cands[d["name"]]
        # IC50
        meas_inserts.append({
            "candidate_id": cid,
            "metric_name": "IC50",
            "value": d["ic50"],
            "unit": "nM",
            "assay_type": "cell_line"
        })
        # DAR
        meas_inserts.append({
            "candidate_id": cid,
            "metric_name": "DAR",
            "value": d["dar"],
            "unit": "ratio",
            "assay_type": "nominal"
        })
        # Aggregation (Mock)
        meas_inserts.append({
            "candidate_id": cid,
            "metric_name": "Aggregation_pct",
            "value": 1.5 + (d["dar"] * 0.3),
            "unit": "%",
            "assay_type": "sec"
        })

    await db.table("golden_measurements").insert(meas_inserts).execute()
    print("Seeding v3 completed successfully.")

if __name__ == "__main__":
    pass
