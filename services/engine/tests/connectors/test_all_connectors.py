"""
Tests for All Connectors (Batch)
모든 커넥터의 기본 기능 테스트
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestUniProtConnector:
    """UniProt 커넥터 테스트"""

    @pytest.fixture
    def connector(self, mock_db):
        from app.connectors.uniprot import UniProtConnector

        return UniProtConnector(mock_db)

    def test_source(self, connector):
        assert connector.source == "uniprot"

    @pytest.mark.asyncio
    async def test_build_queries_with_ids(self, connector):
        queries = await connector.build_queries({"uniprot_ids": ["P04626", "P00533"]})
        assert len(queries) == 2

    @pytest.mark.asyncio
    async def test_build_queries_with_genes(self, connector):
        queries = await connector.build_queries({"gene_symbols": ["ERBB2", "EGFR"]})
        assert len(queries) == 2

    def test_normalize_record(self, connector, mock_uniprot_response):
        normalized = connector.normalize(mock_uniprot_response)

        assert normalized is not None
        assert normalized.external_id == "P04626"
        assert normalized.source == "uniprot"
        assert "ERBB2" in normalized.data.get("gene_symbol", "")


class TestOpenTargetsConnector:
    """Open Targets 커넥터 테스트"""

    @pytest.fixture
    def connector(self, mock_db):
        from app.connectors.opentargets import OpenTargetsConnector

        return OpenTargetsConnector(mock_db)

    def test_source(self, connector):
        assert connector.source == "opentargets"

    @pytest.mark.asyncio
    async def test_build_queries(self, connector):
        queries = await connector.build_queries({"ensembl_ids": ["ENSG00000141736"]})
        assert len(queries) == 1
        assert queries[0].query == "ENSG00000141736"

    def test_normalize_record(self, connector):
        record = {
            "target_id": "ENSG00000141736",
            "target_symbol": "ERBB2",
            "target_name": "erb-b2 receptor tyrosine kinase 2",
            "associations": [
                {
                    "disease": {"id": "EFO_0000305", "name": "breast carcinoma"},
                    "score": 0.8,
                }
            ],
        }

        normalized = connector.normalize(record)

        assert normalized is not None
        assert normalized.external_id == "ENSG00000141736"
        assert normalized.source == "opentargets"


class TestHPAConnector:
    """HPA 커넥터 테스트"""

    @pytest.fixture
    def connector(self, mock_db):
        from app.connectors.hpa import HPAConnector

        return HPAConnector(mock_db)

    def test_source(self, connector):
        assert connector.source == "hpa"

    @pytest.mark.asyncio
    async def test_build_queries_ensembl(self, connector):
        queries = await connector.build_queries({"ensembl_ids": ["ENSG00000141736"]})
        assert len(queries) == 1
        assert queries[0].params["type"] == "ensembl"

    @pytest.mark.asyncio
    async def test_build_queries_gene(self, connector):
        queries = await connector.build_queries({"gene_symbols": ["ERBB2"]})
        assert len(queries) == 1
        assert queries[0].params["type"] == "gene"

    def test_normalize_record(self, connector):
        record = {
            "Gene": "ERBB2",
            "Ensembl": "ENSG00000141736",
            "Protein name": "Receptor tyrosine-protein kinase erbB-2",
            "Tissue expression": [
                {"Tissue": "breast", "Level": "High", "Reliability": "Enhanced"}
            ],
            "RNA tissue specificity": "Low tissue specificity",
        }

        normalized = connector.normalize(record)

        assert normalized is not None
        assert normalized.source == "hpa"
        assert "tissue_expression" in normalized.data


class TestChEMBLConnector:
    """ChEMBL 커넥터 테스트"""

    @pytest.fixture
    def connector(self, mock_db):
        from app.connectors.chembl import ChEMBLConnector

        return ChEMBLConnector(mock_db)

    def test_source(self, connector):
        assert connector.source == "chembl"

    @pytest.mark.asyncio
    async def test_build_queries_chembl_ids(self, connector):
        queries = await connector.build_queries({"chembl_ids": ["CHEMBL1201583"]})
        assert len(queries) == 1
        assert queries[0].params["type"] == "molecule"

    @pytest.mark.asyncio
    async def test_build_queries_search(self, connector):
        queries = await connector.build_queries({"search": "maytansine"})
        assert len(queries) == 1
        assert queries[0].params["type"] == "search"

    def test_normalize_record(self, connector, mock_chembl_response):
        normalized = connector.normalize(mock_chembl_response)

        assert normalized is not None
        assert normalized.external_id == "CHEMBL1201583"
        assert normalized.source == "chembl"
        assert normalized.data["pref_name"] == "ADO-TRASTUZUMAB EMTANSINE"


class TestPubChemConnector:
    """PubChem 커넥터 테스트"""

    @pytest.fixture
    def connector(self, mock_db):
        from app.connectors.pubchem import PubChemConnector

        return PubChemConnector(mock_db)

    def test_source(self, connector):
        assert connector.source == "pubchem"

    @pytest.mark.asyncio
    async def test_build_queries_cids(self, connector):
        queries = await connector.build_queries({"cids": [2244, 2519]})
        assert len(queries) == 1
        assert queries[0].params["type"] == "cid"

    @pytest.mark.asyncio
    async def test_build_queries_names(self, connector):
        queries = await connector.build_queries({"names": ["aspirin"]})
        assert len(queries) == 1
        assert queries[0].params["type"] == "name"

    def test_normalize_record(self, connector):
        record = {
            "CID": 2244,
            "MolecularFormula": "C9H8O4",
            "MolecularWeight": 180.16,
            "CanonicalSMILES": "CC(=O)OC1=CC=CC=C1C(=O)O",
            "InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
        }

        normalized = connector.normalize(record)

        assert normalized is not None
        assert normalized.external_id == "2244"
        assert normalized.source == "pubchem"
        assert normalized.data["inchi_key"] == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"


class TestClinicalTrialsConnector:
    """ClinicalTrials.gov 커넥터 테스트"""

    @pytest.fixture
    def connector(self, mock_db):
        from app.connectors.clinicaltrials import ClinicalTrialsConnector

        return ClinicalTrialsConnector(mock_db)

    def test_source(self, connector):
        assert connector.source == "clinicaltrials"

    @pytest.mark.asyncio
    async def test_build_queries_conditions(self, connector):
        queries = await connector.build_queries({"conditions": ["breast cancer"]})
        assert len(queries) == 1
        assert queries[0].params["type"] == "condition"

    @pytest.mark.asyncio
    async def test_build_queries_nct_ids(self, connector):
        queries = await connector.build_queries({"nct_ids": ["NCT01120184"]})
        assert len(queries) == 1
        assert queries[0].params["type"] == "nct_ids"

    def test_normalize_record(self, connector, mock_clinicaltrials_response):
        record = mock_clinicaltrials_response["studies"][0]
        normalized = connector.normalize(record)

        assert normalized is not None
        assert normalized.external_id == "NCT01120184"
        assert normalized.source == "clinicaltrials"
        assert "HER2" in normalized.data["brief_title"]


class TestOpenFDAConnector:
    """openFDA 커넥터 테스트"""

    @pytest.fixture
    def connector(self, mock_db):
        from app.connectors.openfda import OpenFDAConnector

        return OpenFDAConnector(mock_db)

    def test_source(self, connector):
        assert connector.source == "openfda"

    @pytest.mark.asyncio
    async def test_build_queries_drug_names(self, connector):
        queries = await connector.build_queries({"drug_names": ["trastuzumab"]})
        assert len(queries) == 1
        assert queries[0].params["type"] == "drug_name"

    @pytest.mark.asyncio
    async def test_build_queries_brand_names(self, connector):
        queries = await connector.build_queries({"brand_names": ["Herceptin"]})
        assert len(queries) == 1
        assert queries[0].params["type"] == "brand_name"

    def test_normalize_record(self, connector, mock_openfda_response):
        record = mock_openfda_response["results"][0]
        record["_query_drug_name"] = "trastuzumab"

        normalized = connector.normalize(record)

        assert normalized is not None
        assert normalized.external_id == "10001234"
        assert normalized.source == "openfda"
        assert normalized.data["serious"] == "1"
