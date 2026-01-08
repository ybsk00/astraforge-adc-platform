"""
RDKit Descriptor Calculator
분자 디스크립터 계산 모듈
"""
import structlog
from typing import Optional, Dict, Any

logger = structlog.get_logger()

# RDKit은 선택적 의존성 (Docker 환경에서만 사용)
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors, Lipinski
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    logger.warning("RDKit not available - descriptor calculation will be simulated")


def calculate_descriptors(smiles: str) -> Optional[Dict[str, Any]]:
    """
    SMILES에서 RDKit 디스크립터 계산
    
    Args:
        smiles: 분자 SMILES 문자열
        
    Returns:
        계산된 디스크립터 딕셔너리 또는 None (실패 시)
    """
    if not RDKIT_AVAILABLE:
        # RDKit 없을 때 시뮬레이션 값 반환
        logger.info("rdkit_simulated", smiles=smiles[:20] if smiles else None)
        return simulate_descriptors(smiles)
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.error("invalid_smiles", smiles=smiles[:50] if smiles else None)
            return None
        
        descriptors = {
            # 기본 물성
            "mw": round(Descriptors.MolWt(mol), 2),
            "logp": round(Descriptors.MolLogP(mol), 2),
            "tpsa": round(Descriptors.TPSA(mol), 2),
            
            # 수소 결합
            "hbd": Lipinski.NumHDonors(mol),
            "hba": Lipinski.NumHAcceptors(mol),
            
            # 구조적 특성
            "rot_bonds": Lipinski.NumRotatableBonds(mol),
            "rings": rdMolDescriptors.CalcNumRings(mol),
            "aromatic_rings": rdMolDescriptors.CalcNumAromaticRings(mol),
            
            # 추가 디스크립터
            "heavy_atoms": Lipinski.HeavyAtomCount(mol),
            "fraction_csp3": round(rdMolDescriptors.CalcFractionCSP3(mol), 3),
            "num_heteroatoms": rdMolDescriptors.CalcNumHeteroatoms(mol),
        }
        
        logger.info("descriptors_calculated", smiles=smiles[:20], mw=descriptors["mw"])
        return descriptors
        
    except Exception as e:
        logger.error("descriptor_calculation_failed", smiles=smiles[:50] if smiles else None, error=str(e))
        return None


def simulate_descriptors(smiles: str) -> Dict[str, Any]:
    """
    RDKit 없을 때 시뮬레이션 디스크립터 반환
    (개발/테스트용)
    """
    # SMILES 길이 기반 간단한 추정치
    length = len(smiles) if smiles else 0
    
    return {
        "mw": length * 10 + 100,  # 가상값
        "logp": 2.5,
        "tpsa": 80.0,
        "hbd": 2,
        "hba": 5,
        "rot_bonds": 5,
        "rings": 2,
        "aromatic_rings": 1,
        "heavy_atoms": length // 2,
        "fraction_csp3": 0.3,
        "num_heteroatoms": 3,
        "_simulated": True  # 시뮬레이션 표시
    }


def validate_smiles(smiles: str) -> bool:
    """SMILES 유효성 검사"""
    if not smiles or not isinstance(smiles, str):
        return False
    
    if not RDKIT_AVAILABLE:
        # RDKit 없으면 기본 검사만
        return len(smiles) > 0 and not smiles.isspace()
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False
