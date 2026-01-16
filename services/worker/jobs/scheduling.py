"""
Arq Worker Scheduling Configuration
주기 작업 스케줄링 설정

스케줄:
- PubMed: 매일 04:00 (야간)
- UniProt/Open Targets/HPA: 매주 일요일 02:00
- ChEMBL/PubChem: 매주 수요일 02:00
- ClinicalTrials/openFDA: 매주 토요일 02:00
"""
from typing import Dict, Any

from arq import cron


# ============================================================
# Cron Schedule Definitions
# ============================================================

def get_cron_schedules():
    """
    주기 작업 스케줄 정의
    
    Returns:
        cron job 목록
    """
    return [
        # PubMed - 매일 04:00 (증분 수집)
        cron(
            pubmed_daily_sync,
            hour=4,
            minute=0,
            run_at_startup=False,
        ),
        
        # UniProt - 매주 일요일 02:00
        cron(
            uniprot_weekly_sync,
            weekday=6,  # Sunday
            hour=2,
            minute=0,
            run_at_startup=False,
        ),
        
        # Open Targets - 매주 일요일 03:00
        cron(
            opentargets_weekly_sync,
            weekday=6,
            hour=3,
            minute=0,
            run_at_startup=False,
        ),
        
        # HPA - 매주 일요일 04:00
        cron(
            hpa_weekly_sync,
            weekday=6,
            hour=4,
            minute=0,
            run_at_startup=False,
        ),
        
        # ChEMBL - 매주 수요일 02:00
        cron(
            chembl_weekly_sync,
            weekday=2,  # Wednesday
            hour=2,
            minute=0,
            run_at_startup=False,
        ),
        
        # PubChem - 매주 수요일 03:00
        cron(
            pubchem_weekly_sync,
            weekday=2,
            hour=3,
            minute=0,
            run_at_startup=False,
        ),
        
        # ClinicalTrials - 매주 토요일 02:00
        cron(
            clinicaltrials_weekly_sync,
            weekday=5,  # Saturday
            hour=2,
            minute=0,
            run_at_startup=False,
        ),
        
        # openFDA - 매주 토요일 03:00
        cron(
            openfda_weekly_sync,
            weekday=5,
            hour=3,
            minute=0,
            run_at_startup=False,
        ),
        
        # Fingerprint 재계산 - 매일 05:00
        cron(
            fingerprint_daily_compute,
            hour=5,
            minute=0,
            run_at_startup=False,
        ),
        
        # DB 작업 폴링 - 매 1분마다
        cron(
            db_job_polling,
            minute={i for i in range(60)},
            run_at_startup=True,
        ),
    ]


# ============================================================
# Scheduled Job Functions
# ============================================================

async def pubmed_daily_sync(ctx: Dict[str, Any]):
    """PubMed 일일 증분 수집"""
    from jobs.pubmed_job import pubmed_fetch_job
    
    # 최근 7일 논문 수집
    seed = {
        "query": "antibody drug conjugate OR ADC therapy",
        "retmax": 500,
        "reldate": 7  # 최근 7일
    }
    
    return await pubmed_fetch_job(ctx, seed)


async def uniprot_weekly_sync(ctx: Dict[str, Any]):
    """UniProt 주간 타겟 동기화"""
    from jobs.uniprot_job import uniprot_sync_job
    
    # 주요 ADC 타겟 목록
    seed = {
        "uniprot_ids": [
            "P04626", "P00533", "P21860",  # HER family
            "P11836", "P08637", "P20963",  # Blood cancer targets
            "P16422", "Q15116", "Q9NZQ7",  # Solid tumor / Immune
        ]
    }
    
    return await uniprot_sync_job(ctx, seed)


async def opentargets_weekly_sync(ctx: Dict[str, Any]):
    """Open Targets 주간 동기화"""
    from jobs.meta_sync_job import opentargets_sync_job
    
    seed = {
        "ensembl_ids": [
            "ENSG00000141736",  # ERBB2
            "ENSG00000146648",  # EGFR
            "ENSG00000156127",  # BATF
        ]
    }
    
    return await opentargets_sync_job(ctx, seed)


async def hpa_weekly_sync(ctx: Dict[str, Any]):
    """HPA 주간 동기화"""
    from jobs.meta_sync_job import hpa_sync_job
    
    seed = {"gene_symbols": ["ERBB2", "EGFR", "CD19", "CD20"]}
    
    return await hpa_sync_job(ctx, seed)


async def chembl_weekly_sync(ctx: Dict[str, Any]):
    """ChEMBL 주간 동기화"""
    from jobs.meta_sync_job import chembl_sync_job
    
    seed = {
        "search": "maytansine OR MMAE OR PBD dimer",
        "limit": 100
    }
    
    return await chembl_sync_job(ctx, seed)


async def pubchem_weekly_sync(ctx: Dict[str, Any]):
    """PubChem 주간 동기화"""
    from jobs.meta_sync_job import pubchem_sync_job
    
    seed = {
        "names": ["maytansine", "mertansine", "MMAE", "MMAF"]
    }
    
    return await pubchem_sync_job(ctx, seed)


async def clinicaltrials_weekly_sync(ctx: Dict[str, Any]):
    """ClinicalTrials 주간 동기화"""
    from jobs.clinical_job import clinicaltrials_sync_job
    
    seed = {
        "conditions": ["HER2 positive cancer"],
        "interventions": ["antibody drug conjugate"]
    }
    
    return await clinicaltrials_sync_job(ctx, seed)


async def openfda_weekly_sync(ctx: Dict[str, Any]):
    """openFDA 주간 동기화"""
    from jobs.clinical_job import openfda_sync_job
    
    seed = {
        "drug_names": ["trastuzumab", "brentuximab", "polatuzumab"]
    }
    
    return await openfda_sync_job(ctx, seed)


async def fingerprint_daily_compute(ctx: Dict[str, Any]):
    """
    Fingerprint 일일 재계산
    
    pending_compute 상태인 화합물의 fingerprint 계산
    """
    import os
    from supabase import create_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        return {"status": "error", "message": "Supabase not configured"}
    
    db = create_client(supabase_url, supabase_key)
    
    # pending_compute 상태인 화합물 조회
    pending = db.table("component_catalog").select(
        "id, smiles"
    ).eq("status", "pending_compute").not_.is_("smiles", "null").limit(100).execute()
    
    if not pending.data:
        return {"status": "idle", "processed": 0}
    
    try:
        from app.services.fingerprint import FingerprintService
        service = FingerprintService(db)
    except ImportError:
        return {"status": "error", "message": "RDKit not available"}
    
    processed = 0
    errors = 0
    
    for compound in pending.data:
        try:
            # Fingerprint 계산
            fp_result = service.compute_fingerprint(compound["smiles"])
            descriptors = service.compute_descriptors(compound["smiles"])
            
            if fp_result and descriptors:
                # 상태 업데이트
                db.table("component_catalog").update({
                    "status": "active",
                    "properties": {
                        "rdkit": {
                            "fingerprint_bits": fp_result["on_bit_count"],
                            **descriptors
                        }
                    }
                }).eq("id", compound["id"]).execute()
                
                processed += 1
            else:
                # 실패 시 상태 변경
                db.table("component_catalog").update({
                    "status": "failed"
                }).eq("id", compound["id"]).execute()
                
                errors += 1
                
        except Exception:
            errors += 1
    
    return {
        "status": "completed",
        "processed": processed,
        "errors": errors
    }


async def db_job_polling(ctx: Dict[str, Any]):
    """
    DB 대기 중인 작업을 폴링하여 실행합니다.
    """
    from jobs.worker import poll_db_jobs
    return await poll_db_jobs(ctx)
