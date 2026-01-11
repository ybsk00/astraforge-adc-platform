import httpx
import structlog
from typing import Any, Optional, Dict, List
from datetime import datetime

logger = structlog.get_logger()

class ResolverService:
    """
    Seed 데이터의 외부 ID를 정규화하는 서비스
    """
    
    OT_API_URL = "https://api.platform.opentargets.org/api/v4/graphql"
    
    def __init__(self, db_client=None):
        self.db = db_client
        self.logger = logger.bind(service="resolver")

    async def resolve_target(self, gene_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Gene Symbol을 기반으로 Ensembl ID를 찾음
        """
        query = """
        query targetSearch($queryString: String!) {
          search(queryString: $queryString, entityNames: ["target"]) {
            hits {
              id
              name
              entity
            }
          }
        }
        """
        variables = {"queryString": gene_symbol}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.OT_API_URL,
                    json={"query": query, "variables": variables}
                )
                response.raise_for_status()
                data = response.json()
                
                hits = data.get("data", {}).get("search", {}).get("hits", [])
                if not hits:
                    return None
                
                # 첫 번째 검색 결과 사용 (정확도 순)
                best_match = hits[0]
                return {
                    "ensembl_gene_id": best_match["id"],
                    "gene_symbol": gene_symbol
                }
        except Exception as e:
            self.logger.error("resolve_target_failed", gene_symbol=gene_symbol, error=str(e))
            return None

    async def resolve_disease(self, disease_name: str) -> Optional[Dict[str, Any]]:
        """
        질환명을 기반으로 EFO ID를 찾음
        """
        query = """
        query diseaseSearch($queryString: String!) {
          search(queryString: $queryString, entityNames: ["disease"]) {
            hits {
              id
              name
              entity
            }
          }
        }
        """
        variables = {"queryString": disease_name}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.OT_API_URL,
                    json={"query": query, "variables": variables}
                )
                response.raise_for_status()
                data = response.json()
                
                hits = data.get("data", {}).get("search", {}).get("hits", [])
                if not hits:
                    return None
                
                best_match = hits[0]
                return {
                    "ontology_id": best_match["id"],
                    "ontology_source": "EFO" if best_match["id"].startswith("EFO") else "MONDO",
                    "disease_name": disease_name
                }
        except Exception as e:
            self.logger.error("resolve_disease_failed", disease_name=disease_name, error=str(e))
            return None

    async def resolve_seed_set(self, seed_set_id: str) -> Dict[str, Any]:
        """
        Seed Set에 포함된 모든 엔티티의 외부 ID를 채움
        """
        if not self.db:
            return {"status": "error", "message": "DB client not provided"}
        
        stats = {"targets_resolved": 0, "diseases_resolved": 0, "errors": 0}
        
        # 1. 타겟 정규화
        try:
            targets_res = self.db.table("seed_set_targets").select("entity_targets(*)").eq("seed_set_id", seed_set_id).execute()
            for row in targets_res.data:
                target = row.get("entity_targets")
                if target and not target.get("ensembl_gene_id"):
                    resolved = await self.resolve_target(target["gene_symbol"])
                    if resolved:
                        self.db.table("entity_targets").update({
                            "ensembl_gene_id": resolved["ensembl_gene_id"]
                        }).eq("id", target["id"]).execute()
                        stats["targets_resolved"] += 1
                        self.logger.info("target_resolved", gene_symbol=target["gene_symbol"], ensembl_id=resolved["ensembl_gene_id"])
        except Exception as e:
            self.logger.error("target_resolution_loop_failed", error=str(e))
            stats["errors"] += 1

        # 2. 질환 정규화
        try:
            diseases_res = self.db.table("seed_set_diseases").select("entity_diseases(*)").eq("seed_set_id", seed_set_id).execute()
            for row in diseases_res.data:
                disease = row.get("entity_diseases")
                if disease and not disease.get("ontology_id"):
                    resolved = await self.resolve_disease(disease["disease_name"])
                    if resolved:
                        self.db.table("entity_diseases").update({
                            "ontology_id": resolved["ontology_id"],
                            "ontology_source": resolved["ontology_source"]
                        }).eq("id", disease["id"]).execute()
                        stats["diseases_resolved"] += 1
                        self.logger.info("disease_resolved", disease_name=disease["disease_name"], ontology_id=resolved["ontology_id"])
        except Exception as e:
            self.logger.error("disease_resolution_loop_failed", error=str(e))
            stats["errors"] += 1
            
        return {
            "status": "completed",
            "stats": stats,
            "seed_set_id": seed_set_id
        }
