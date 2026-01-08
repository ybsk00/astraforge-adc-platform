"""
Pytest Fixtures
공통 테스트 픽스처 정의
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime


# ============================================================
# Event Loop
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================
# Mock Database Client
# ============================================================

@pytest.fixture
def mock_db():
    """Mock Supabase client"""
    db = MagicMock()
    
    # Table mock
    table_mock = MagicMock()
    
    # Select chain
    table_mock.select.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.ilike.return_value = table_mock
    table_mock.order.return_value = table_mock
    table_mock.limit.return_value = table_mock
    table_mock.range.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[], count=0)
    
    # Insert/Update/Upsert
    table_mock.insert.return_value = table_mock
    table_mock.update.return_value = table_mock
    table_mock.upsert.return_value = table_mock
    table_mock.delete.return_value = table_mock
    
    db.table.return_value = table_mock
    
    return db


# ============================================================
# Mock HTTP Responses
# ============================================================

@pytest.fixture
def mock_pubmed_response():
    """Mock PubMed ESearch/EFetch response"""
    esearch_response = """<?xml version="1.0"?>
    <eSearchResult>
        <Count>100</Count>
        <RetMax>10</RetMax>
        <RetStart>0</RetStart>
        <IdList>
            <Id>12345678</Id>
            <Id>12345679</Id>
        </IdList>
    </eSearchResult>"""
    
    efetch_response = """<?xml version="1.0"?>
    <PubmedArticleSet>
        <PubmedArticle>
            <MedlineCitation>
                <PMID>12345678</PMID>
                <Article>
                    <ArticleTitle>Test Article Title</ArticleTitle>
                    <Abstract>
                        <AbstractText>This is a test abstract.</AbstractText>
                    </Abstract>
                </Article>
            </MedlineCitation>
        </PubmedArticle>
    </PubmedArticleSet>"""
    
    return {"esearch": esearch_response, "efetch": efetch_response}


@pytest.fixture
def mock_uniprot_response():
    """Mock UniProt response"""
    return {
        "primaryAccession": "P04626",
        "uniProtkbId": "ERBB2_HUMAN",
        "organism": {"scientificName": "Homo sapiens", "taxonId": 9606},
        "genes": [{"geneName": {"value": "ERBB2"}}],
        "proteinDescription": {
            "recommendedName": {"fullName": {"value": "Receptor tyrosine-protein kinase erbB-2"}}
        },
        "comments": [{
            "commentType": "FUNCTION",
            "texts": [{"value": "Protein tyrosine kinase that is part of several cell surface receptor complexes."}]
        }],
        "uniProtKBCrossReferences": [
            {"database": "Ensembl", "id": "ENSG00000141736"},
            {"database": "HGNC", "id": "HGNC:3430"}
        ]
    }


@pytest.fixture
def mock_opentargets_response():
    """Mock Open Targets GraphQL response"""
    return {
        "data": {
            "target": {
                "id": "ENSG00000141736",
                "approvedSymbol": "ERBB2",
                "approvedName": "erb-b2 receptor tyrosine kinase 2",
                "biotype": "protein_coding",
                "associatedDiseases": {
                    "count": 100,
                    "rows": [
                        {
                            "disease": {
                                "id": "EFO_0000305",
                                "name": "breast carcinoma",
                                "therapeuticAreas": [{"id": "MONDO_0045024", "name": "cancer"}]
                            },
                            "score": 0.8,
                            "datatypeScores": [{"id": "literature", "score": 0.5}]
                        }
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_chembl_response():
    """Mock ChEMBL response"""
    return {
        "molecule_chembl_id": "CHEMBL1201583",
        "pref_name": "ADO-TRASTUZUMAB EMTANSINE",
        "molecule_type": "Protein",
        "max_phase": 4,
        "therapeutic_flag": True,
        "molecule_structures": {
            "canonical_smiles": None,
            "standard_inchi": None,
            "standard_inchi_key": None
        },
        "molecule_properties": {
            "mw_freebase": 150000,
            "alogp": None
        }
    }


@pytest.fixture
def mock_pubchem_response():
    """Mock PubChem response"""
    return {
        "PropertyTable": {
            "Properties": [{
                "CID": 2244,
                "MolecularFormula": "C9H8O4",
                "MolecularWeight": 180.16,
                "CanonicalSMILES": "CC(=O)OC1=CC=CC=C1C(=O)O",
                "InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                "IUPACName": "2-acetyloxybenzoic acid"
            }]
        }
    }


@pytest.fixture
def mock_clinicaltrials_response():
    """Mock ClinicalTrials.gov response"""
    return {
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT01120184",
                        "briefTitle": "Study of T-DM1 in HER2+ Breast Cancer"
                    },
                    "statusModule": {
                        "overallStatus": "COMPLETED",
                        "enrollmentInfo": {"count": 500}
                    },
                    "designModule": {
                        "phases": ["PHASE3"],
                        "studyType": "INTERVENTIONAL"
                    },
                    "conditionsModule": {
                        "conditions": ["HER2 Positive Breast Cancer"]
                    },
                    "armsInterventionsModule": {
                        "interventions": [
                            {"type": "DRUG", "name": "T-DM1", "description": "ADC drug"}
                        ]
                    }
                }
            }
        ],
        "nextPageToken": None
    }


@pytest.fixture
def mock_openfda_response():
    """Mock openFDA response"""
    return {
        "meta": {"results": {"total": 1000}},
        "results": [
            {
                "safetyreportid": "10001234",
                "receivedate": "20230101",
                "serious": "1",
                "seriousnessdeath": "0",
                "patient": {
                    "patientsex": "2",
                    "patientonsetage": "50",
                    "reaction": [
                        {"reactionmeddrapt": "Nausea", "reactionoutcome": "1"}
                    ],
                    "drug": [
                        {"medicinalproduct": "TRASTUZUMAB", "drugcharacterization": "1"}
                    ]
                }
            }
        ]
    }


# ============================================================
# Mock HTTP Client
# ============================================================

@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_response.text = ""
    mock_response.raise_for_status.return_value = None
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    
    return mock_client


# ============================================================
# Sample Data
# ============================================================

@pytest.fixture
def sample_target():
    """Sample target component"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "type": "target",
        "name": "HER2",
        "properties": {
            "uniprot_id": "P04626",
            "gene_symbol": "ERBB2",
            "organism": "Homo sapiens"
        },
        "status": "active"
    }


@pytest.fixture  
def sample_payload():
    """Sample payload component"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "type": "payload",
        "name": "DM1",
        "properties": {
            "smiles": "C[C@H]1C[C@@H]...",
            "mechanism": "tubulin_inhibitor"
        },
        "status": "active"
    }
