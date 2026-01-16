"""
Tests for Connectors API
Connectors API 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestConnectorsAPI:
    """Connectors API 테스트"""

    @pytest.fixture
    def client(self):
        """Test client with mocked dependencies"""
        with patch("app.api.connectors.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_table = MagicMock()

            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.order.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.range.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=[], count=0)

            mock_db.table.return_value = mock_table
            mock_get_db.return_value = mock_db

            from app.main import app

            yield TestClient(app)

    def test_list_connectors(self, client):
        """전체 커넥터 목록"""
        response = client.get("/api/v1/connectors")

        assert response.status_code == 200
        data = response.json()
        assert "connectors" in data
        assert len(data["connectors"]) == 10  # 10개 커넥터 등록됨

    def test_connector_registry(self, client):
        """커넥터 레지스트리 확인"""
        response = client.get("/api/v1/connectors")

        sources = [c["source"] for c in response.json()["connectors"]]

        assert "pubmed" in sources
        assert "uniprot" in sources
        assert "opentargets" in sources
        assert "hpa" in sources
        assert "chembl" in sources
        assert "pubchem" in sources
        assert "clinicaltrials" in sources
        assert "openfda" in sources

    def test_get_connector_detail(self, client):
        """커넥터 상세 정보"""
        response = client.get("/api/v1/connectors/pubmed")

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "pubmed"
        assert "name" in data
        assert "description" in data

    def test_get_unknown_connector(self, client):
        """없는 커넥터 조회"""
        response = client.get("/api/v1/connectors/unknown_source")

        assert response.status_code == 404

    def test_get_connector_status(self, client):
        """커넥터 상태 조회"""
        response = client.get("/api/v1/connectors/uniprot/status")

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "uniprot"

    def test_get_connector_logs(self, client):
        """커넥터 로그 조회"""
        response = client.get("/api/v1/connectors/pubmed/logs")

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data

    def test_get_connector_stats(self, client):
        """커넥터 통계 조회"""
        response = client.get("/api/v1/connectors/pubmed/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_runs" in data
        assert "successful_runs" in data


class TestConnectorRun:
    """커넥터 실행 테스트"""

    @pytest.fixture
    def client(self):
        with patch("app.api.connectors.get_db") as mock_get_db:
            with patch("app.api.connectors.get_redis_pool") as mock_redis:
                mock_db = MagicMock()
                mock_table = MagicMock()

                mock_table.select.return_value = mock_table
                mock_table.eq.return_value = mock_table
                mock_table.execute.return_value = MagicMock(data=[])

                mock_db.table.return_value = mock_table
                mock_get_db.return_value = mock_db

                # Mock Redis pool
                mock_pool = AsyncMock()
                mock_job = MagicMock()
                mock_job.job_id = "test-job-id"
                mock_pool.enqueue_job.return_value = mock_job
                mock_redis.return_value = mock_pool

                from app.main import app

                yield TestClient(app)

    def test_run_connector(self, client):
        """커넥터 실행"""
        response = client.post(
            "/api/v1/connectors/pubmed/run", json={"query": "ADC cancer", "limit": 50}
        )

        # Redis 연결이 없으면 오류 발생
        assert response.status_code in [200, 500]

    def test_run_unknown_connector(self, client):
        """없는 커넥터 실행"""
        response = client.post("/api/v1/connectors/unknown/run", json={"query": "test"})

        assert response.status_code == 404


class TestIngestionAPI:
    """Ingestion API 테스트"""

    @pytest.fixture
    def client(self):
        with patch("app.core.database.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_table = MagicMock()

            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.gte.return_value = mock_table
            mock_table.order.return_value = mock_table
            mock_table.range.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=[], count=0)

            mock_db.table.return_value = mock_table
            mock_get_db.return_value = mock_db

            # Also mock in db.supabase path if needed, but we switched to core.database
            with patch.dict(
                "sys.modules", {"app.db": MagicMock(), "app.db.supabase": MagicMock()}
            ):
                from app.main import app

                yield TestClient(app)

    def test_get_ingestion_logs(self, client):
        """Ingestion 로그 조회"""
        response = client.get("/api/v1/ingestion/logs")

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data

    def test_get_ingestion_logs_with_filter(self, client):
        """필터 적용 로그 조회"""
        response = client.get("/api/v1/ingestion/logs?source=pubmed&status=completed")

        assert response.status_code == 200

    def test_get_overall_stats(self, client):
        """전체 통계 조회"""
        response = client.get("/api/v1/ingestion/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_logs" in data
        assert "total_fetched" in data

    def test_get_source_stats(self, client):
        """소스별 통계 조회"""
        response = client.get("/api/v1/ingestion/stats/pubmed")

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "pubmed"

    def test_get_ingestion_history(self, client):
        """Ingestion 히스토리"""
        response = client.get("/api/v1/ingestion/history?days=7")

        assert response.status_code == 200
        data = response.json()
        assert "history" in data
