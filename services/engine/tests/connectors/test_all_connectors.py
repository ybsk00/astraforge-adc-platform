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
        assert normalized is None

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
        assert normalized is None

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
        assert normalized is None

    def test_normalize_record(self, connector, mock_chembl_response):
        normalized = connector.normalize(mock_chembl_response)
        assert normalized is None

    def test_normalize_record(self, connector):
        record = {
            "CID": 2244,
            "MolecularFormula": "C9H8O4",
            "MolecularWeight": 180.16,
            "CanonicalSMILES": "CC(=O)OC1=CC=CC=C1C(=O)O",
            "InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
        }
        normalized = connector.normalize(record)
        assert normalized is None

    def test_normalize_record(self, connector, mock_openfda_response):
        record = mock_openfda_response["results"][0]
        record["_query_drug_name"] = "trastuzumab"
        normalized = connector.normalize(record)
        assert normalized is None
