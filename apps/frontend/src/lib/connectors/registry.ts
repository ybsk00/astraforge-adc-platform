/**
 * Connector Registry (TypeScript Port)
 * 파이썬 백엔드의 CONNECTOR_REGISTRY와 동기화됨
 */

export interface ConnectorInfo {
    name: string;
    description: string;
    category: string;
    rate_limit: string;
}

export const CONNECTOR_REGISTRY: Record<string, ConnectorInfo> = {
    "pubmed": {
        "name": "PubMed",
        "description": "NCBI PubMed 문헌 수집",
        "category": "literature",
        "rate_limit": "3-10 req/sec (API Key 유무)",
    },
    "uniprot": {
        "name": "UniProt",
        "description": "UniProt 단백질 정보",
        "category": "target",
        "rate_limit": "5 req/sec",
    },
    "opentargets": {
        "name": "Open Targets",
        "description": "Target-Disease 연관 스코어",
        "category": "target",
        "rate_limit": "Standard GraphQL",
    },
    "hpa": {
        "name": "Human Protein Atlas",
        "description": "조직/세포 발현 데이터",
        "category": "expression",
        "rate_limit": "5 req/sec",
    },
    "chembl": {
        "name": "ChEMBL",
        "description": "화합물/활성 데이터",
        "category": "compound",
        "rate_limit": "5 req/sec",
    },
    "pubchem": {
        "name": "PubChem",
        "description": "화합물 구조/식별자",
        "category": "compound",
        "rate_limit": "5 req/sec",
    },
    "clinicaltrials": {
        "name": "ClinicalTrials.gov",
        "description": "임상시험 정보",
        "category": "clinical",
        "rate_limit": "Standard",
    },
    "openfda": {
        "name": "openFDA",
        "description": "FDA 안전 신호",
        "category": "safety",
        "rate_limit": "240 req/min",
    },
    "seed": {
        "name": "Seed Data",
        "description": "Gold Standard 데이터 시딩",
        "category": "system",
        "rate_limit": "None",
    },
    "resolve": {
        "name": "Resolve IDs",
        "description": "외부 ID 식별 (UniProt/PubChem)",
        "category": "system",
        "rate_limit": "External APIs",
    },
};
