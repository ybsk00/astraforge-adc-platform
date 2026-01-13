"""
Connector Framework - Base Classes and Utilities
공통 인터페이스, Rate Limiter, Retry 정책
"""
import asyncio
import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Dict, List
import httpx
import structlog
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential,
    retry_if_exception_type
)

logger = structlog.get_logger()


# ============================================================
# Data Types
# ============================================================

@dataclass
class QuerySpec:
    """쿼리 명세"""
    query: str
    params: Dict[str, Any] = field(default_factory=dict)
    

@dataclass
class CursorState:
    """커서 상태"""
    cursor_id: str
    source: str
    position: Dict[str, Any] = field(default_factory=dict)
    stats: Dict[str, int] = field(default_factory=lambda: {
        "fetched": 0,
        "new": 0,
        "updated": 0,
        "errors": 0
    })


@dataclass
class FetchResult:
    """Fetch 결과"""
    records: List[Dict[str, Any]]
    has_more: bool
    next_cursor: Dict[str, Any] = field(default_factory=dict)
    raw_response: Optional[Any] = None


@dataclass
class NormalizedRecord:
    """정규화된 레코드"""
    external_id: str
    record_type: str  # target, linker, payload, literature 등
    data: Dict[str, Any]
    checksum: str
    source: str
    
    @staticmethod
    def compute_checksum(data: Dict[str, Any]) -> str:
        """데이터 체크섬 계산"""
        import json
        content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class UpsertResult:
    """Upsert 결과"""
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    errors: int = 0
    ids: List[str] = field(default_factory=list)


# ============================================================
# Rate Limiter
# ============================================================

class RateLimiter:
    """
    소스별 Rate Limiting
    
    사용법:
        limiter = RateLimiter(qps=3.0)  # 초당 3회
        await limiter.acquire()
        response = await client.get(url)
    """
    
    def __init__(self, qps: float = 1.0):
        """
        Args:
            qps: Queries per second (requests per second)
        """
        self.interval = 1.0 / qps if qps > 0 else 0
        self.last_call = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """다음 요청 전 대기"""
        async with self._lock:
            now = time.monotonic()
            wait_time = self.last_call + self.interval - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.last_call = time.monotonic()


# ============================================================
# HTTP Client with Retry
# ============================================================

class RetryableHTTPError(Exception):
    """재시도 가능한 HTTP 에러"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


async def fetch_with_retry(
    url: str,
    rate_limiter: Optional[RateLimiter] = None,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> httpx.Response:
    """
    Rate limit + Retry가 적용된 HTTP 요청
    
    Args:
        url: 요청 URL
        rate_limiter: Rate limiter 인스턴스
        method: HTTP 메서드
        headers: 헤더
        params: 쿼리 파라미터
        json_data: JSON body
        timeout: 타임아웃 (초)
        max_retries: 최대 재시도 횟수
    
    Returns:
        httpx.Response
    """
    
    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((RetryableHTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def _fetch():
        if rate_limiter:
            await rate_limiter.acquire()
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, params=params, json=json_data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Rate limit (429) 또는 서버 에러 (5xx)는 재시도
            if response.status_code == 429:
                logger.warning("rate_limit_hit", url=url, status=429)
                raise RetryableHTTPError(429, "Rate limited")
            
            if response.status_code >= 500:
                logger.warning("server_error", url=url, status=response.status_code)
                raise RetryableHTTPError(response.status_code, "Server error")
            
            response.raise_for_status()
            return response
    
    return await _fetch()


# ============================================================
# Base Connector
# ============================================================

class BaseConnector(ABC):
    """
    커넥터 기본 클래스
    
    모든 커넥터는 이 클래스를 상속하여 구현합니다.
    
    구현해야 할 메서드:
        - build_queries: seed에서 쿼리 목록 생성
        - fetch_page: 한 페이지 데이터 조회
        - normalize: 원본 레코드를 정규화
        - upsert: 정규화된 레코드를 저장
    """
    
    # 자식 클래스에서 설정
    source: str = ""
    rate_limit_qps: float = 1.0
    max_retries: int = 3
    
    def __init__(self, db_client = None):
        """
        Args:
            db_client: Supabase 클라이언트
        """
        self.db = db_client
        self.rate_limiter = RateLimiter(qps=self.rate_limit_qps)
        self.logger = logger.bind(connector=self.source)
    
    @abstractmethod
    async def build_queries(self, seed: Dict[str, Any]) -> List[QuerySpec]:
        """
        시드 데이터에서 쿼리 목록 생성
        
        Args:
            seed: 시드 데이터 (예: {"keywords": ["ADC", "HER2"]})
        
        Returns:
            쿼리 명세 목록
        """
        pass
    
    @abstractmethod
    async def fetch_page(
        self, 
        query: QuerySpec, 
        cursor: CursorState
    ) -> FetchResult:
        """
        한 페이지 데이터 조회
        
        Args:
            query: 쿼리 명세
            cursor: 현재 커서 상태
        
        Returns:
            조회 결과
        """
        pass
    
    @abstractmethod
    def normalize(self, record: Dict[str, Any]) -> Optional[NormalizedRecord]:
        """
        원본 레코드를 정규화
        
        Args:
            record: 원본 레코드
        
        Returns:
            정규화된 레코드 (실패 시 None)
        """
        pass
    
    @abstractmethod
    async def upsert(
        self, 
        records: List[NormalizedRecord]
    ) -> UpsertResult:
        """
        정규화된 레코드를 DB에 저장
        
        Args:
            records: 정규화된 레코드 목록
        
        Returns:
            저장 결과
        """
        pass
    
    async def save_raw_data(
        self, 
        raw_items: List[Dict[str, Any]], 
        query_profile: str, 
        dataset_version: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        RAW 데이터 저장 (필수)
        
        Args:
            raw_items: 원본 데이터 목록
            query_profile: 쿼리 프로파일 이름
            dataset_version: 데이터셋 버전
            metadata: 추가 메타데이터 (query_target 등)
            
        Returns:
            저장된 RAW ID 목록
        """
        if not raw_items:
            return []
            
        import json
        
        # 테이블명 결정 (기본: golden_seed_raw, 문헌: literature_raw)
        table_name = "golden_seed_raw"
        if self.source in ["pubmed", "biorxiv"]:
            table_name = "literature_raw"
            
        rows = []
        for item in raw_items:
            # Source ID 추출 (기본: id 필드)
            source_id = str(item.get("id") or item.get("nctId") or item.get("pmid") or "unknown")
            
            # Content Hash
            content_dump = json.dumps(item, sort_keys=True)
            content_hash = hashlib.sha256(content_dump.encode()).hexdigest()
            
            row = {
                "source": self.source,
                "source_id": source_id,
                "source_hash": content_hash,
                "raw_payload": item,
                "query_profile": query_profile,
                "dataset_version": dataset_version,
                "fetched_at": datetime.utcnow().isoformat()
            }
            if metadata:
                row.update(metadata)
                
            rows.append(row)
            
        # Bulk Upsert
        try:
            # Note: Supabase-py bulk upsert might need chunking for large sets
            res = self.db.table(table_name).upsert(
                rows, 
                on_conflict="source,source_hash",
                ignore_duplicates=True 
            ).execute()
            
            # Return IDs (if available, otherwise empty)
            return [r["id"] for r in (res.data or [])]
            
        except Exception as e:
            self.logger.error("save_raw_failed", error=str(e))
            raise e

    async def run(
        self, 
        seed: Dict[str, Any], 
        cursor: Optional[CursorState] = None,
        max_pages: int = 100
    ) -> Dict[str, Any]:
        """
        전체 수집 프로세스 실행 (Standardized)
        
        Args:
            seed: 시드 데이터 (Must contain 'profile_name' or 'query_profile')
            cursor: 시작 커서
            max_pages: 최대 페이지 수
        
        Returns:
            실행 결과 통계
        """
        start_time = time.time()
        stats = {"fetched": 0, "new": 0, "updated": 0, "errors": 0, "raw_saved": 0}
        
        profile_name = seed.get("profile_name") or seed.get("query_profile")
        dataset_version = seed.get("dataset_version", "v1")
        
        try:
            queries = await self.build_queries(seed)
            self.logger.info("queries_built", count=len(queries), profile=profile_name)
            
            for query in queries:
                page_count = 0
                current_cursor = cursor or CursorState(
                    cursor_id="", 
                    source=self.source
                )
                
                while page_count < max_pages:
                    # 1. Fetch
                    result = await self.fetch_page(query, current_cursor)
                    stats["fetched"] += len(result.records)
                    
                    if not result.records:
                        break
                    
                    # 2. Save RAW (Mandatory)
                    if profile_name:
                        try:
                            raw_ids = await self.save_raw_data(
                                result.records, 
                                profile_name, 
                                dataset_version,
                                metadata={"query": query.query}
                            )
                            stats["raw_saved"] += len(raw_ids)
                        except Exception as e:
                            self.logger.error("raw_save_error", error=str(e))
                            # RAW 저장 실패는 치명적이지 않게 처리할지 결정 (여기서는 진행)
                    
                    # 3. Normalize
                    normalized = []
                    for record in result.records:
                        try:
                            norm = self.normalize(record)
                            if norm:
                                normalized.append(norm)
                        except Exception as e:
                            stats["errors"] += 1
                            self.logger.warning("normalize_failed", error=str(e))
                    
                    # 4. Upsert Candidates (Optional - if normalize implemented)
                    if normalized:
                        upsert_result = await self.upsert(normalized)
                        stats["new"] += upsert_result.inserted
                        stats["updated"] += upsert_result.updated
                        stats["errors"] += upsert_result.errors
                    
                    # Next page
                    if not result.has_more:
                        break
                    
                    current_cursor.position = result.next_cursor
                    page_count += 1
            
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.info("run_completed", stats=stats, duration_ms=duration_ms)
            
            return {
                "status": "completed",
                "stats": stats,
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            self.logger.error("run_failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "stats": stats
            }


# ============================================================
# Utility Functions
# ============================================================

def generate_query_hash(source: str, query: str, params: Dict[str, Any]) -> str:
    """쿼리 해시 생성 (커서 식별용)"""
    import json
    content = f"{source}:{query}:{json.dumps(params, sort_keys=True)}"
    return hashlib.md5(content.encode()).hexdigest()[:12]
