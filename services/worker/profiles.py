"""
Query Profile Registry
Defines standard query profiles for different connectors and purposes.
"""

QUERY_PROFILES = {
    # === ClinicalTrials.gov ===
    "target_enrichment": {
        "description": "Broad collection of trials for a specific target in oncology",
        "connector": "clinicaltrials",
        "mode": "target_centric",
        "query_template": "({target} OR {synonyms}) AND (cancer OR tumor OR carcinoma OR neoplasm OR metastatic OR lymphoma OR leukemia OR myeloma OR sarcoma OR malignan*)",
        "filters": {"overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED"},
    },
    "adc_signal_boost": {
        "description": "Target enrichment with ADC keyword boosting (for ranking)",
        "connector": "clinicaltrials",
        "mode": "target_centric",
        "query_template": "({target} OR {synonyms}) AND (cancer OR tumor OR carcinoma OR neoplasm OR metastatic OR lymphoma OR leukemia OR myeloma OR sarcoma OR malignan*)",
        "boost_keywords": [
            "antibody-drug conjugate",
            "antibody drug conjugate",
            "immunoconjugate",
            "antibody conjugate",
            "ADC",
            "vedotin",
            "deruxtecan",
            "govitecan",
            "ozogamicin",
            "soravtansine",
        ],
    },
    # === PubMed ===
    "payload_discovery": {
        "description": "Find payloads associated with a target",
        "connector": "pubmed",
        "mode": "discovery",
        "query_template": '"{target}" AND (payload OR warhead OR cytotoxic OR toxin OR PROTAC OR immune agonist) AND (conjugate OR ADC OR antibody)',
    },
    "linker_discovery": {
        "description": "Find linkers associated with a target",
        "connector": "pubmed",
        "mode": "discovery",
        "query_template": '"{target}" AND (cleavable linker OR non-cleavable OR valine-citrulline OR hydrazone OR disulfide)',
    },
    "tox_risk": {
        "description": "Identify toxicity risks for a payload",
        "connector": "pubmed",
        "mode": "risk",
        "query_template": '"{payload}" AND (toxicity OR neutropenia OR ILD OR hepatotoxicity)',
    },
    "bystander_risk": {
        "description": "Check for bystander effect evidence",
        "connector": "pubmed",
        "mode": "risk",
        "query_template": '"{payload}" AND bystander AND ADC',
    },
    # === PubChem ===
    "payload_smiles_enrichment": {
        "description": "Fetch SMILES and properties for payload candidates",
        "connector": "pubchem",
        "mode": "enrichment",
    },
    # === ChEMBL ===
    "payload_family_expand": {
        "description": "Expand payload candidates based on family/mechanism",
        "connector": "chembl",
        "mode": "expansion",
    },
}


def get_profile(name: str):
    return QUERY_PROFILES.get(name)
