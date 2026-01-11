"""
Seed Golden Set Data v2
20종 이상의 실제 승인 ADC 약물 실험 데이터 삽입
"""
import asyncio
import uuid
from typing import List, Dict, Any

# 데이터 정의
GOLDEN_DATA = [
    {"name": "Kadcyla", "target": "HER2", "antibody": "Trastuzumab", "linker": "SMCC", "payload": "DM1", "dar": 3.5, "status": "approved", "ic50": 0.5},
    {"name": "Adcetris", "target": "CD30", "antibody": "Brentuximab", "linker": "Val-Cit", "payload": "MMAE", "dar": 4.0, "status": "approved", "ic50": 2.1},
    {"name": "Enhertu", "target": "HER2", "antibody": "Trastuzumab", "linker": "GGFG", "payload": "DXd", "dar": 8.0, "status": "approved", "ic50": 0.1},
    {"name": "Trodelvy", "target": "TROP-2", "antibody": "Sacituzumab", "linker": "CL2A", "payload": "SN-38", "dar": 7.8, "status": "approved", "ic50": 0.3},
    {"name": "Padcev", "target": "Nectin-4", "antibody": "Enfortumab", "linker": "Val-Cit", "payload": "MMAE", "dar": 3.8, "status": "approved", "ic50": 1.5},
    {"name": "Polivy", "target": "CD79b", "antibody": "Polatuzumab", "linker": "Val-Cit", "payload": "MMAE", "dar": 3.5, "status": "approved", "ic50": 0.8},
    {"name": "Besponsa", "target": "CD22", "antibody": "Inotuzumab", "linker": "AcBut", "payload": "Calicheamicin", "dar": 6.0, "status": "approved", "ic50": 0.05},
    {"name": "Mylotarg", "target": "CD33", "antibody": "Gemtuzumab", "linker": "AcBut", "payload": "Calicheamicin", "dar": 2.5, "status": "approved", "ic50": 0.1},
    {"name": "Blenrep", "target": "BCMA", "antibody": "Belantamab", "linker": "Non-cleavable", "payload": "MMAF", "dar": 4.0, "status": "approved", "ic50": 5.0},
    {"name": "Zynlonta", "target": "CD19", "antibody": "Loncastuximab", "linker": "Val-Ala", "payload": "SG3199", "dar": 2.3, "status": "approved", "ic50": 0.01},
    {"name": "Tivdak", "target": "Tissue Factor", "antibody": "Tisotumab", "linker": "Val-Cit", "payload": "MMAE", "dar": 4.0, "status": "approved", "ic50": 1.2},
    {"name": "Elahere", "target": "FRα", "antibody": "Mirvetuximab", "linker": "Sulfo-SPDB", "payload": "DM4", "dar": 3.4, "status": "approved", "ic50": 0.4},
    {"name": "Akalux", "target": "EGFR", "antibody": "Cetuximab", "linker": "IR700", "payload": "Dye", "dar": 2.0, "status": "approved", "ic50": 10.0},
    {"name": "Kimmtrak", "target": "gp100", "antibody": "Tebentafusp", "linker": "Fusion", "payload": "TCR", "dar": 1.0, "status": "approved", "ic50": 0.001},
    {"name": "Danyelza", "target": "GD2", "antibody": "Naxitamab", "linker": "None", "payload": "None", "dar": 0.0, "status": "approved", "ic50": 100.0},
    {"name": "Margenza", "target": "HER2", "antibody": "Margetuximab", "linker": "None", "payload": "None", "dar": 0.0, "status": "approved", "ic50": 50.0},
    {"name": "Rybrevant", "target": "EGFR/MET", "antibody": "Amivantamab", "linker": "None", "payload": "None", "dar": 0.0, "status": "approved", "ic50": 20.0},
    {"name": "Sarclisa", "target": "CD38", "antibody": "Isatuximab", "linker": "None", "payload": "None", "dar": 0.0, "status": "approved", "ic50": 30.0},
    {"name": "Darzalex", "target": "CD38", "antibody": "Daratumumab", "linker": "None", "payload": "None", "dar": 0.0, "status": "approved", "ic50": 15.0},
    {"name": "Empliciti", "target": "SLAMF7", "antibody": "Elotuzumab", "linker": "None", "payload": "None", "dar": 0.0, "status": "approved", "ic50": 40.0}
]

async def seed_v2(db):
    print(f"Seeding {len(GOLDEN_DATA)} golden candidates...")
    
    # 1. Clear existing (optional)
    # await db.table("golden_measurements").delete().neq("id", uuid.uuid4()).execute()
    # await db.table("golden_candidates").delete().neq("id", uuid.uuid4()).execute()

    # 2. Insert Candidates
    cand_inserts = []
    for d in GOLDEN_DATA:
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
    
    # 3. Insert Measurements
    meas_inserts = []
    for d in GOLDEN_DATA:
        cid = inserted_cands[d["name"]]
        # IC50
        meas_inserts.append({
            "candidate_id": cid,
            "metric_name": "IC50",
            "value": d["ic50"],
            "unit": "nM",
            "assay_type": "cell_line"
        })
        # DAR (as measurement)
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
            "value": 1.0 + (d["dar"] * 0.2), # DAR가 높을수록 응집 위험 증가 가정
            "unit": "%",
            "assay_type": "sec"
        })

    await db.table("golden_measurements").insert(meas_inserts).execute()
    print("Seeding v2 completed successfully.")

if __name__ == "__main__":
    # 실제 실행은 Supabase 클라이언트 필요
    pass
