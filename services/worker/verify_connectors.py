import sys
import os
import asyncio

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "services", "engine"))

from services.worker.profiles import QUERY_PROFILES
from services.engine.app.connectors.clinicaltrials import ClinicalTrialsConnector
from services.engine.app.connectors.pubmed import PubMedConnector
from services.engine.app.connectors.pubchem import PubChemConnector
from services.engine.app.connectors.chembl import ChEMBLConnector


async def verify():
    print("Verifying imports...")
    print(f"Loaded {len(QUERY_PROFILES)} query profiles.")

    print("Instantiating connectors...")
    ct_conn = ClinicalTrialsConnector(None)
    pm_conn = PubMedConnector(None)
    pc_conn = PubChemConnector(None)
    cb_conn = ChEMBLConnector(None)

    print(f"ClinicalTrialsConnector: {ct_conn.source}")
    print(f"PubMedConnector: {pm_conn.source}")
    print(f"PubChemConnector: {pc_conn.source}")
    print(f"ChEMBLConnector: {cb_conn.source}")

    print("Verification successful!")


if __name__ == "__main__":
    asyncio.run(verify())
