"""
Tests for Base Connector Framework
BaseConnector, RateLimiter, common utilities 테스트
"""

import pytest
from datetime import datetime

import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.connectors.base import (
    BaseConnector,
    QuerySpec,
    FetchResult,
    NormalizedRecord,
    UpsertResult,
    RateLimiter,
    generate_query_hash,
)


class TestQuerySpec:
    """QuerySpec 테스트"""

    def test_create_query_spec(self):
        """QuerySpec 생성"""
        spec = QuerySpec(query="test query", params={"key": "value"})

        assert spec.query == "test query"
        assert spec.params == {"key": "value"}

    def test_query_spec_default_params(self):
        """기본 params는 빈 dict"""
        spec = QuerySpec(query="test")

        assert spec.params == {}

    def test_create_normalized_record(self):
        """NormalizedRecord 생성"""
        record = NormalizedRecord(
            external_id="12345",
            record_type="literature",
            data={"title": "Test"},
            checksum="abc123",
            source="pubmed",
        )

        assert record.external_id == "12345"
        assert record.record_type == "literature"
        assert record.data == {"title": "Test"}
        assert record.checksum == "abc123"
        assert record.source == "pubmed"

    def test_compute_checksum(self):
        """checksum 계산 테스트"""
        data1 = {"title": "Test", "abstract": "Content"}
        data2 = {"title": "Test", "abstract": "Content"}
        data3 = {"title": "Different", "abstract": "Content"}

        checksum1 = NormalizedRecord.compute_checksum(data1)
        checksum2 = NormalizedRecord.compute_checksum(data2)
        checksum3 = NormalizedRecord.compute_checksum(data3)

        assert checksum1 == checksum2  # 같은 데이터는 같은 checksum
        assert checksum1 != checksum3  # 다른 데이터는 다른 checksum
        assert len(checksum1) == 16  # SHA256 hex truncated to 16


class TestUpsertResult:
    """UpsertResult 테스트"""

    def test_create_upsert_result(self):
        """UpsertResult 생성"""
        result = UpsertResult()

        assert result.inserted == 0
        assert result.updated == 0
        assert result.unchanged == 0
        assert result.errors == 0
        assert result.ids == []

    def test_upsert_result_counts(self):
        """카운트 누적"""
        result = UpsertResult()
        result.inserted = 5
        result.updated = 3
        result.unchanged = 2
        result.errors = 1
        result.ids = ["id1", "id2"]

        assert result.inserted == 5
        assert result.updated == 3
        assert result.unchanged == 2
        assert result.errors == 1
        assert len(result.ids) == 2


class TestRateLimiter:
    """RateLimiter 테스트"""

    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """기본 rate limiting"""
        limiter = RateLimiter(qps=10.0)

        start = datetime.now()

        # 3번 연속 호출
        await limiter.acquire()
        await limiter.acquire()
        await limiter.acquire()

        elapsed = (datetime.now() - start).total_seconds()

        # 최소 대기 시간 (0.1초 * 2 = 0.2초)
        assert elapsed >= 0.15  # 약간의 오차 허용

    @pytest.mark.asyncio
    async def test_rate_limiter_high_qps(self):
        """높은 QPS에서 빠른 처리"""
        limiter = RateLimiter(qps=1000.0)

        start = datetime.now()

        for _ in range(10):
            await limiter.acquire()

        elapsed = (datetime.now() - start).total_seconds()

        # 높은 QPS에서는 거의 즉시
        assert elapsed < 0.5


class TestGenerateQueryHash:
    """generate_query_hash 테스트"""

    def test_hash_consistency(self):
        """같은 입력에 같은 해시"""
        hash1 = generate_query_hash("pubmed", "cancer", {"retmax": 100})
        hash2 = generate_query_hash("pubmed", "cancer", {"retmax": 100})

        assert hash1 == hash2

    def test_hash_different_source(self):
        """다른 소스는 다른 해시"""
        hash1 = generate_query_hash("pubmed", "cancer", {})
        hash2 = generate_query_hash("uniprot", "cancer", {})

        assert hash1 != hash2

    def test_hash_different_params(self):
        """다른 params는 다른 해시"""
        hash1 = generate_query_hash("pubmed", "cancer", {"retmax": 100})
        hash2 = generate_query_hash("pubmed", "cancer", {"retmax": 200})

        assert hash1 != hash2


class TestBaseConnector:
    """BaseConnector 추상 클래스 테스트"""

    def test_cannot_instantiate_abstract(self):
        """추상 클래스는 직접 인스턴스화 불가"""
        with pytest.raises(TypeError):
            BaseConnector()  # type: ignore

    def test_concrete_implementation(self, mock_db):
        """구체 클래스 구현 테스트"""

        class TestConnector(BaseConnector):
            source = "test"
            rate_limit_qps = 5.0

            async def build_queries(self, seed):
                return [QuerySpec(query=seed.get("query", ""))]

            async def fetch_page(self, query, cursor):
                return FetchResult(records=[{"id": "1"}], has_more=False)

            def normalize(self, record):
                return NormalizedRecord(
                    external_id=record["id"],
                    record_type="test",
                    data=record,
                    checksum="test",
                    source="test",
                )

            async def upsert(self, records):
                return UpsertResult(inserted=len(records))

        connector = TestConnector(mock_db)

        assert connector.source == "test"
        assert connector.rate_limit_qps == 5.0
        assert connector.db == mock_db

    @pytest.mark.asyncio
    async def test_run_method(self, mock_db):
        """run() 메서드 테스트"""

        class TestConnector(BaseConnector):
            source = "test"

            async def build_queries(self, seed):
                return [QuerySpec(query="test")]

            async def fetch_page(self, query, cursor):
                return FetchResult(records=[{"id": "1"}, {"id": "2"}], has_more=False)

            def normalize(self, record):
                return NormalizedRecord(
                    external_id=record["id"],
                    record_type="test",
                    data=record,
                    checksum=f"hash_{record['id']}",
                    source="test",
                )

            async def upsert(self, records):
                return UpsertResult(inserted=len(records))

        connector = TestConnector(mock_db)

        result = await connector.run(seed={"query": "test"}, max_pages=1)

        assert "stats" in result
        assert "duration_ms" in result
        assert result["stats"]["fetched"] == 2
