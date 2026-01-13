# Linker & Payload Standardization Dictionaries

# 1. Payload Dictionary (표준명 매핑)
PAYLOAD_DICTIONARY = {
    # Auristatins
    "monomethyl auristatin e": "MMAE",
    "mmae": "MMAE",
    "vedotin": "MMAE",
    "monomethyl auristatin f": "MMAF",
    "mmaf": "MMAF",
    "mafodotin": "MMAF",
    
    # Maytansinoids
    "emtansine": "DM1",
    "dm1": "DM1",
    "ravtansine": "DM4",
    "dm4": "DM4",
    
    # Camptothecins / Topoisomerase I inhibitors
    "deruxtecan": "DXd",
    "dxd": "DXd",
    "sn-38": "SN-38",
    "sn38": "SN-38",
    "govetecan": "SN-38",
    "exatecan": "Exatecan",
    
    # DNA Damaging Agents (PBDs)
    "tesirine": "SG3199",
    "talirine": "SGD-1910",
    "pbd": "PBD_Generic",
    
    # Others
    "calicheamicin": "Calicheamicin",
    "ozogamicin": "Calicheamicin",
}

# 2. Linker Dictionary (표준명 매핑)
LINKER_DICTIONARY = {
    # Cleavable (Enzymatic)
    "valine-citrulline": "VC",
    "vc": "VC",
    "val-cit": "VC",
    "mc-vc-pab": "Mc-VC-PAB",
    "ggfg": "GGFG",
    
    # Cleavable (pH / Acid)
    "hydrazone": "Hydrazone",
    "acid-labile": "Hydrazone",
    
    # Cleavable (Reducible)
    "disulfide": "Disulfide",
    "spdb": "SPDB",
    
    # Non-Cleavable
    "mcc": "MCC",
    "smcc": "SMCC",
    "maleimidocaproyl": "MC",
    "mc": "MC",
    "non-cleavable": "Non-Cleavable",
    "stable": "Non-Cleavable",
}

# 3. Target Normalization (Simple Mapping)
TARGET_DICTIONARY = {
    "her2": "HER2",
    "erbb2": "HER2",
    "trop2": "TROP2",
    "tacstd2": "TROP2",
    "cd30": "CD30",
    "tnfrsf8": "CD30",
    "cd33": "CD33",
    "siglec-3": "CD33",
    "cd22": "CD22",
    "cd19": "CD19",
    "cd79b": "CD79b",
    "bcma": "BCMA",
    "tnfrsf17": "BCMA",
    "nectin-4": "Nectin-4",
    "folr1": "FOLR1",
    "folate receptor alpha": "FOLR1",
    "tissue factor": "TF",
    "f3": "TF",
    "cd123": "CD123",
    "il3ra": "CD123",
    "c-met": "c-MET",
    "met": "c-MET",
    "egfr": "EGFR",
    "her1": "EGFR",
}

# 6. IO Blocklist (Exclude these from Target-Centric Collection)
IO_BLOCKLIST = [
    "pembrolizumab", "keytruda",
    "nivolumab", "opdivo",
    "atezolizumab", "tecentriq",
    "durvalumab", "imfinzi",
    "avelumab", "bavencio",
    "cemiplimab", "libtayo",
    "dostarlimab", "jemperli",
    "ipilimumab", "yervoy",
    "tremelimumab", "imjudo",
    "spartalizumab",
    "tislelizumab",
    "toripalimab",
    "sintilimab",
    "camrelizumab",
    "pd-1", "pd-l1", "ctla-4",
    "pd1", "pdl1", "ctla4",
    "programmed cell death",
    "checkpoint inhibitor"
]

# 4. Target Lists (Solid / Heme)
TARGET_LIST_SOLID = [
    "HER2", "HER3", "TROP2", "NECTIN4", "FOLR1", "SLC39A6", "CD276", "MSLN", "MET", "EGFR", 
    "CLDN18", "F3", "TPBG", "SLC34A2", "PTK7", "ROR1", "AXL", "CEACAM5", "MUC1", "EPCAM", 
    "GPC3", "FOLH1", "MUC16", "STEAP1", "ICAM1"
]

TARGET_LIST_HEME = [
    "CD19", "CD22", "CD30", "CD79B", "CD33", "IL3RA", "TNFRSF17", "CD37", "CD38", "SDC1", 
    "CD70", "CD74", "FLT3", "KIT", "SLAMF7", "CD24", "CD47", "CD52", "CD20", "CD66", 
    "CCR4", "CXCR4", "CD25", "CD71", "CD45"
]

# 5. Target Synonyms (For Query Construction)
TARGET_SYNONYMS = {
    "HER2": ["ERBB2"],
    "TROP2": ["TACSTD2"],
    "NECTIN4": ["PVRL4"],
    "FOLR1": ["FRα", "Folate receptor alpha"],
    "CLDN18": ["Claudin 18.2"],
    "SLC34A2": ["NaPi2b"],
    "TNFRSF17": ["BCMA"],
    "IL3RA": ["CD123"],
    "SDC1": ["CD138"],
    "CD20": ["MS4A1"],
    "CD25": ["IL2RA"],
    "CD71": ["TFRC"],
    "CD45": ["PTPRC"],
    "TPBG": ["5T4"],
    "FOLH1": ["PSMA"],
    "CD66": ["CEACAM"],
}
