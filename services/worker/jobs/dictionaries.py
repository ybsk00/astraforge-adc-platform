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
