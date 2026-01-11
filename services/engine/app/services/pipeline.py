import structlog
from typing import Any, Dict, List, Optional
from app.services.resolver import ResolverService
from app.connectors.pubmed import PubMedConnector
from app.connectors.opentargets import OpenTargetsConnector
# 추가 커넥터들은 필요 시 임포트

logger = structlog.get_logger()

class PipelineService:
    """
    Seed Set 기반 전체 수집 파이프라인 관리 서비스
    """
    
    def __init__(self, db_client=None):
        self.db = db_client
        self.resolver = ResolverService(db_client)
        self.logger = logger.bind(service="pipeline")
        
    async def run_seed_set(
        self, 
        seed_set_id: str, 
        connector_names: Optional[List[str]] = None,
        max_pages: int = 10
    ) -> Dict[str, Any]:
        """
        Seed Set에 대한 전체 수집 프로세스 실행
        
        1. Resolver 실행: Seed 데이터의 외부 ID(Ensembl, EFO 등) 정규화
        2. Connectors 실행: 선택된 소스들로부터 데이터 수집
        """
        self.logger.info("pipeline_started", seed_set_id=seed_set_id)
        
        # 1. Resolver 단계 (ID 정규화)
        # 모든 커넥터 실행 전 최신 ID 정보를 확보하기 위해 실행
        resolve_result = await self.resolver.resolve_seed_set(seed_set_id)
        self.logger.info("resolution_completed", stats=resolve_result["stats"])
        
        # 2. 커넥터 실행 단계
        results = {}
        
        # 커넥터 인스턴스 맵
        # TODO: 커넥터 팩토리 또는 레지스트리 패턴으로 확장 가능
        connector_map = {
            "pubmed": PubMedConnector(self.db),
            "opentargets": OpenTargetsConnector(self.db),
        }
        
        # 실행할 커넥터 결정 (지정되지 않으면 전체 실행)
        target_connectors = connector_names if connector_names else list(connector_map.keys())
        
        for name in target_connectors:
            if name not in connector_map:
                self.logger.warning("unknown_connector_skipped", connector=name)
                continue
                
            self.logger.info("running_connector", connector=name)
            connector = connector_map[name]
            
            try:
                # Seed Set ID를 포함하여 커넥터 실행
                # 커넥터 내부의 build_queries에서 seed_set_id를 처리함
                run_result = await connector.run(
                    seed={"seed_set_id": seed_set_id},
                    max_pages=max_pages
                )
                results[name] = run_result
                self.logger.info("connector_completed", 
                                connector=name, 
                                status=run_result.get("status"),
                                stats=run_result.get("stats"))
            except Exception as e:
                self.logger.error("connector_execution_failed", 
                                 connector=name, 
                                 error=str(e))
                results[name] = {"status": "failed", "error": str(e)}
                
        return {
            "status": "completed",
            "seed_set_id": seed_set_id,
            "results": results,
            "resolution_stats": resolve_result["stats"]
        }
