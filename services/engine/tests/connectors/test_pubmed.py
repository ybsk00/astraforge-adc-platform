"""
Tests for PubMed Connector
PubMed 커넥터 유닛 테스트
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.connectors.pubmed import PubMedConnector
from app.connectors.base import QuerySpec, NormalizedRecord


class TestPubMedConnector:
    """PubMed 커넥터 테스트"""

    @pytest.fixture
    def connector(self, mock_db):
        """PubMed 커넥터 인스턴스"""
        return PubMedConnector(mock_db)

    def test_connector_source(self, connector):
        """소스 이름 확인"""
        assert connector.source == "pubmed"

    def test_connector_rate_limit(self, connector):
        """Rate limit 확인"""
        assert connector.rate_limit_qps == 3.0  # 기본값

    @pytest.mark.asyncio
    async def test_build_queries_with_query(self, connector):
        """쿼리 문자열로 빌드"""
        queries = await connector.build_queries({"query": "ADC cancer"})

        assert len(queries) == 1
        assert queries[0].query == "ADC cancer"

    @pytest.mark.asyncio
    async def test_build_queries_with_pmids(self, connector):
        """PMID 목록으로 빌드"""
        queries = await connector.build_queries({"pmids": ["12345678", "12345679"]})

        assert len(queries) == 1
        assert "12345678" in queries[0].query
        assert "12345679" in queries[0].query

    def test_normalize_record(self, connector):
        record = {"pmid": "12345678", "title": "Test"}
        normalized = connector.normalize(record)

        assert normalized is None

    @pytest.mark.asyncio
    async def test_fetch_page_esearch(self, connector, mock_pubmed_response):
        """ESearch/EFetch 호출 테스트"""
        # 변수들은 통합 테스트에서 사용됨 (현재 stub)
        _ = QuerySpec(query="cancer ADC", params={"type": "search"})

        _mock_response = MagicMock()
        _mock_response.status_code = 200
        _mock_response.text = mock_pubmed_response["esearch"]

        with patch(
            "app.connectors.pubmed.fetch_with_retry", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = _mock_response

            # 실제 API 호출 없이 테스트
            # 이 테스트는 통합 테스트로 분리해야 함
            pass

    @pytest.mark.asyncio
    async def test_upsert_records(self, connector, mock_db):
        """레코드 upsert 테스트"""
        records = [
            NormalizedRecord(
                external_id="12345678",
                record_type="literature",
                data={"title": "Test 1"},
                checksum="hash1",
                source="pubmed",
            ),
            NormalizedRecord(
                external_id="12345679",
                record_type="literature",
                data={"title": "Test 2"},
                checksum="hash2",
                source="pubmed",
            ),
        ]

        result = await connector.upsert(records)

        # Mock이므로 실제 upsert는 일어나지 않음
        # 에러 없이 완료되는지 확인
        assert result is not None


@pytest.mark.skip(reason="RAW First strategy: normalization is skipped")
class TestPubMedNormalization:
    """PubMed 정규화 상세 테스트"""

    @pytest.fixture
    def connector(self, mock_db):
        return PubMedConnector(mock_db)

    def test_normalize_full_record(self, connector):
        """전체 필드가 있는 레코드"""
        record = {
            "pmid": "99999999",
            "title": "Complete Record Title",
            "abstract": "Full abstract text here.",
            "authors": ["Smith J", "Doe A", "Kim B"],
            "journal": "Nature Medicine",
            "pub_date": "2024-06-15",
            "doi": "10.1234/nm.2024.001",
            "keywords": ["ADC", "HER2", "Cancer"],
            "mesh_terms": ["Breast Neoplasms", "Drug Conjugates"],
        }

        normalized = connector.normalize(record)

        assert normalized.external_id == "99999999"
        assert normalized.data["title"] == "Complete Record Title"
        assert "Full abstract" in normalized.data["abstract"]
        assert len(normalized.data.get("authors", [])) == 3

    def test_normalize_minimal_record(self, connector):
        """최소 필드만 있는 레코드"""
        record = {"pmid": "11111111", "title": "Minimal Title"}

        normalized = connector.normalize(record)

        assert normalized is not None
        assert normalized.external_id == "11111111"
        assert normalized.data["title"] == "Minimal Title"

    def test_checksum_changes_with_content(self, connector):
        """내용이 바뀌면 checksum도 변경"""
        record1 = {"pmid": "12345", "title": "Title A", "abstract": "Abstract A"}
        record2 = {"pmid": "12345", "title": "Title A", "abstract": "Abstract B"}

        norm1 = connector.normalize(record1)
        norm2 = connector.normalize(record2)

        assert norm1.checksum != norm2.checksum
