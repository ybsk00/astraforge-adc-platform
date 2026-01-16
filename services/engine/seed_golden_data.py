"""
Seed Golden Set Data
Kadcyla, Adcetris, Enhertu 등 주요 약물의 실험 데이터 삽입
"""

import uuid
from supabase import create_client

# Supabase 설정 (환경 변수 가정)
URL = "YOUR_SUPABASE_URL"
KEY = "YOUR_SUPABASE_KEY"


async def seed_golden_set():
    supabase = create_client(URL, KEY)

    # 1. Golden Candidates
    candidates = [
        {
            "id": str(uuid.uuid4()),
            "drug_name": "Kadcyla",
            "target": "HER2",
            "antibody": "Trastuzumab",
            "linker": "SMCC",
            "payload": "DM1",
            "dar_nominal": 3.5,
            "approval_status": "approved",
        },
        {
            "id": str(uuid.uuid4()),
            "drug_name": "Adcetris",
            "target": "CD30",
            "antibody": "Brentuximab",
            "linker": "Val-Cit",
            "payload": "MMAE",
            "dar_nominal": 4.0,
            "approval_status": "approved",
        },
    ]

    res = await supabase.table("golden_candidates").insert(candidates).execute()
    cands = res.data

    # 2. Golden Measurements
    measurements = []
    for c in cands:
        if c["drug_name"] == "Kadcyla":
            measurements.extend(
                [
                    {
                        "candidate_id": c["id"],
                        "metric_name": "IC50",
                        "value": 0.5,
                        "unit": "nM",
                        "assay_type": "cell_line",
                    },
                    {
                        "candidate_id": c["id"],
                        "metric_name": "Aggregation_pct",
                        "value": 1.2,
                        "unit": "%",
                        "assay_type": "sec",
                    },
                ]
            )
        elif c["drug_name"] == "Adcetris":
            measurements.extend(
                [
                    {
                        "candidate_id": c["id"],
                        "metric_name": "IC50",
                        "value": 2.1,
                        "unit": "nM",
                        "assay_type": "cell_line",
                    },
                    {
                        "candidate_id": c["id"],
                        "metric_name": "Aggregation_pct",
                        "value": 0.8,
                        "unit": "%",
                        "assay_type": "sec",
                    },
                ]
            )

    await supabase.table("golden_measurements").insert(measurements).execute()
    print("Golden Set Seeding Completed.")


if __name__ == "__main__":
    # 실제 실행 시에는 URL/KEY 설정 필요
    # asyncio.run(seed_golden_set())
    pass
