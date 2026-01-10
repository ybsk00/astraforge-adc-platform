import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase() -> Client:
    return create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    )

async def populate_seeds():
    db = get_supabase()
    
    # 1. 암종 데이터 (entity_diseases)
    diseases = [
        {"disease_name": "Breast cancer", "disease_group": "solid", "search_term": "breast cancer"},
        {"disease_name": "Non-small cell lung cancer", "disease_group": "solid", "search_term": "non small cell lung cancer"},
        {"disease_name": "Small cell lung cancer", "disease_group": "solid", "search_term": "small cell lung cancer"},
        {"disease_name": "Colorectal cancer", "disease_group": "solid", "search_term": "colorectal cancer"},
        {"disease_name": "Gastric cancer", "disease_group": "solid", "search_term": "gastric cancer"},
        {"disease_name": "Pancreatic cancer", "disease_group": "solid", "search_term": "pancreatic cancer"},
        {"disease_name": "Ovarian cancer", "disease_group": "solid", "search_term": "ovarian cancer"},
        {"disease_name": "Multiple myeloma", "disease_group": "heme", "search_term": "multiple myeloma"},
        {"disease_name": "Acute myeloid leukemia", "disease_group": "heme", "search_term": "acute myeloid leukemia"},
    ]
    
    print("Populating diseases...")
    for d in diseases:
        db.table("entity_diseases").upsert(d, on_conflict="disease_name").execute()

    # 2. 표적 데이터 (entity_targets) - Top 50만 우선 삽입
    targets = [
        {"gene_symbol": "EGFR"}, {"gene_symbol": "ERBB2"}, {"gene_symbol": "ERBB3"}, {"gene_symbol": "ALK"},
        {"gene_symbol": "MET"}, {"gene_symbol": "KRAS"}, {"gene_symbol": "BRAF"}, {"gene_symbol": "PIK3CA"},
        {"gene_symbol": "CD19"}, {"gene_symbol": "MS4A1"}, {"gene_symbol": "CD22"}, {"gene_symbol": "TNFRSF17"},
        {"gene_symbol": "TACSTD2"}, {"gene_symbol": "NECTIN4"}, {"gene_symbol": "FOLR1"}, {"gene_symbol": "CLDN18"},
        {"gene_symbol": "CEACAM5"}, {"gene_symbol": "MUC16"}, {"gene_symbol": "EPCAM"}, {"gene_symbol": "PDCD1"},
        {"gene_symbol": "CD274"}, {"gene_symbol": "CTLA4"}, {"gene_symbol": "LAG3"}, {"gene_symbol": "TIGIT"},
    ]
    
    print("Populating targets...")
    for t in targets:
        db.table("entity_targets").upsert(t, on_conflict="gene_symbol").execute()

    # 3. 약물 데이터 (entity_drugs)
    drugs = [
        {"drug_name": "Trastuzumab", "drug_class": "mAb"},
        {"drug_name": "Pembrolizumab", "drug_class": "mAb"},
        {"drug_name": "Osimertinib", "drug_class": "small_molecule"},
        {"drug_name": "Trastuzumab deruxtecan", "drug_class": "ADC"},
        {"drug_name": "Sacituzumab govitecan", "drug_class": "ADC"},
        {"drug_name": "MMAE", "drug_class": "payload"},
        {"drug_name": "DXd", "drug_class": "payload"},
    ]
    
    print("Populating drugs...")
    for dr in drugs:
        db.table("entity_drugs").upsert(dr, on_conflict="drug_name").execute()

    # 4. Seed Set 생성
    print("Creating default seed set...")
    seed_set = {"seed_set_name": "default_oncology_v1", "description": "Top targets + core cancers + core drugs (MVP)"}
    res = db.table("seed_sets").upsert(seed_set, on_conflict="seed_set_name").execute()
    seed_set_id = res.data[0]["id"]

    # 5. 연결 (Join Tables)
    print("Linking entities to seed set...")
    
    # Diseases 연결
    disease_ids = db.table("entity_diseases").select("id").execute().data
    for d_id in disease_ids:
        db.table("seed_set_diseases").upsert({"seed_set_id": seed_set_id, "disease_id": d_id["id"]}, on_conflict="seed_set_id,disease_id").execute()
        
    # Targets 연결
    target_ids = db.table("entity_targets").select("id").execute().data
    for t_id in target_ids:
        db.table("seed_set_targets").upsert({"seed_set_id": seed_set_id, "target_id": t_id["id"]}, on_conflict="seed_set_id,target_id").execute()
        
    # Drugs 연결
    drug_ids = db.table("entity_drugs").select("id").execute().data
    for dr_id in drug_ids:
        db.table("seed_set_drugs").upsert({"seed_set_id": seed_set_id, "drug_id": dr_id["id"]}, on_conflict="seed_set_id,drug_id").execute()

    print("Done!")

if __name__ == "__main__":
    asyncio.run(populate_seeds())
