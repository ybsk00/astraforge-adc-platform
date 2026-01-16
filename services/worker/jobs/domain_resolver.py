import structlog
from typing import Dict, Any, List
from supabase import Client
from datetime import datetime

logger = structlog.get_logger()


async def resolve_entities(ctx: Dict[str, Any], seed_set_id: str):
    """
    시드 세트에 포함된 엔티티들의 외부 ID를 해결(Resolve)합니다.
    - Diseases: search_term -> EFO ID (Open Targets 활용)
    - Targets: gene_symbol -> Ensembl ID, UniProt Accession
    - Drugs: drug_name -> ChEMBL ID, PubChem CID
    """
    db: Client = ctx["db"]
    log = logger.bind(seed_set_id=seed_set_id)

    log.info("entity_resolution_started")

    # 1. Targets Resolution
    target_results = (
        db.table("seed_set_targets")
        .select("target_id, entity_targets(*)")
        .eq("seed_set_id", seed_set_id)
        .execute()
    )
    for row in target_results.data:
        target = row["entity_targets"]
        if not target["ensembl_gene_id"] or not target["uniprot_accession"]:
            # TODO: 실제 외부 API(Open Targets/UniProt) 호출하여 ID 조회
            # 현재는 모킹 또는 간단한 규칙으로 처리 (추후 고도화)
            log.info("resolving_target", symbol=target["gene_symbol"])
            # 예시: 임시 업데이트 (실제로는 API 호출 필요)
            # db.table("entity_targets").update({"ensembl_gene_id": "ENSG...", "uniprot_accession": "P..."}).eq("id", target["id"]).execute()

    # 2. Diseases Resolution
    disease_results = (
        db.table("seed_set_diseases")
        .select("disease_id, entity_diseases(*)")
        .eq("seed_set_id", seed_set_id)
        .execute()
    )
    for row in disease_results.data:
        disease = row["entity_diseases"]
        if not disease["ontology_id"]:
            log.info("resolving_disease", name=disease["disease_name"])
            # TODO: Open Targets API 등을 통해 EFO ID 조회

    log.info("entity_resolution_completed")


async def generate_queries(
    ctx: Dict[str, Any], seed_set_id: str, connector_name: str
) -> List[Dict[str, Any]]:
    """
    시드 세트와 커넥터 타입에 따라 실제 실행할 쿼리 목록을 생성합니다.
    """
    db: Client = ctx["db"]
    queries = []

    # 시드 데이터 로드
    targets = (
        db.table("seed_set_targets")
        .select("entity_targets(gene_symbol, ensembl_gene_id)")
        .eq("seed_set_id", seed_set_id)
        .execute()
        .data
    )
    diseases = (
        db.table("seed_set_diseases")
        .select("entity_diseases(disease_name, search_term, ontology_id)")
        .eq("seed_set_id", seed_set_id)
        .execute()
        .data
    )

    if connector_name == "pubmed":
        # PubMed용 쿼리: (Target) AND (Disease)
        for t in targets:
            symbol = t["entity_targets"]["gene_symbol"]
            for d in diseases:
                d_name = d["entity_diseases"]["disease_name"]
                query_str = f'("{symbol}"[Title/Abstract]) AND ("{d_name}"[Title/Abstract]) AND (cancer OR tumor OR oncology)'
                queries.append(
                    {"query": query_str, "target": symbol, "disease": d_name}
                )

    elif connector_name == "opentargets":
        # Open Targets용 쿼리: Ensembl ID + EFO ID 조합
        for t in targets:
            ensg = t["entity_targets"]["ensembl_gene_id"]
            for d in diseases:
                efo = d["entity_diseases"]["ontology_id"]
                if ensg and efo:
                    queries.append({"target_id": ensg, "disease_id": efo})

    return queries


async def ingest_to_staging(
    ctx: Dict[str, Any],
    component_type: str,
    name: str,
    data: Dict[str, Any],
    source: str,
):
    """
    수집된 데이터를 스테이징 테이블(staging_components)에 저장합니다.
    관리자의 승인을 거쳐 카탈로그에 반영됩니다.
    """
    db: Client = ctx["db"]

    # 중복 확인 (이름 기준)
    existing = (
        db.table("staging_components")
        .select("id")
        .eq("name", name)
        .eq("type", component_type)
        .execute()
    )
    if existing.data:
        logger.info("staging_item_exists", name=name, type=component_type)
        return

    db.table("staging_components").insert(
        {
            "type": component_type,
            "name": name,
            "normalized": data,
            "source_info": {
                "source": source,
                "fetched_at": datetime.utcnow().isoformat(),
            },
            "status": "pending_review",
        }
    ).execute()

    logger.info("ingested_to_staging", name=name, type=component_type)
