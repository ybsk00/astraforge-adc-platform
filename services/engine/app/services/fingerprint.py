"""
RDKit Fingerprint Service
화합물 구조 유사도 검색 및 fingerprint 계산

RDKit 의존성 필요: pip install rdkit
"""
import os
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class SimilarityResult:
    """유사도 검색 결과"""
    compound_id: str
    name: str
    smiles: str
    similarity: float
    fingerprint_type: str


class FingerprintService:
    """
    RDKit 기반 Fingerprint 서비스
    
    지원 fingerprint 타입:
    - morgan: Morgan/Circular fingerprints (ECFP 유사)
    - maccs: MACCS keys (166 bits)
    - topological: Daylight-type topological fingerprints
    """
    
    # 기본 설정
    DEFAULT_RADIUS = 2        # Morgan fingerprint 반경
    DEFAULT_NBITS = 2048      # Fingerprint 비트 수
    DEFAULT_TOP_K = 10        # 기본 반환 개수
    DEFAULT_THRESHOLD = 0.5   # 최소 유사도 임계값
    
    def __init__(self, db_client=None):
        """
        Args:
            db_client: Supabase 클라이언트 (optional, 검색용)
        """
        self.db = db_client
        self.logger = logger.bind(service="fingerprint")
        
        # RDKit 가용성 체크
        self._rdkit_available = self._check_rdkit()
    
    def _check_rdkit(self) -> bool:
        """RDKit 가용성 확인"""
        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem, MACCSkeys
            from rdkit import DataStructs
            return True
        except ImportError:
            self.logger.warning("rdkit_not_available", 
                message="RDKit not installed. Install with: pip install rdkit")
            return False
    
    def compute_fingerprint(
        self, 
        smiles: str, 
        fp_type: str = "morgan",
        radius: int = None,
        n_bits: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        SMILES에서 fingerprint 계산
        
        Args:
            smiles: SMILES 문자열
            fp_type: fingerprint 타입 (morgan, maccs, topological)
            radius: Morgan fingerprint 반경
            n_bits: fingerprint 비트 수
        
        Returns:
            {"fingerprint": bytes, "on_bits": List[int], "type": str}
        """
        if not self._rdkit_available:
            return None
        
        radius = radius or self.DEFAULT_RADIUS
        n_bits = n_bits or self.DEFAULT_NBITS
        
        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem, MACCSkeys
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                self.logger.warning("invalid_smiles", smiles=smiles[:50])
                return None
            
            if fp_type == "morgan":
                fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
            elif fp_type == "maccs":
                fp = MACCSkeys.GenMACCSKeys(mol)
            elif fp_type == "topological":
                fp = Chem.RDKFingerprint(mol, fpSize=n_bits)
            else:
                self.logger.warning("unknown_fp_type", fp_type=fp_type)
                return None
            
            # BitVector를 bytes로 변환
            fp_bytes = fp.ToBitString()
            on_bits = list(fp.GetOnBits())
            
            return {
                "fingerprint": fp_bytes,
                "on_bits": on_bits,
                "on_bit_count": len(on_bits),
                "total_bits": fp.GetNumBits(),
                "type": fp_type
            }
            
        except Exception as e:
            self.logger.error("fingerprint_compute_failed", error=str(e), smiles=smiles[:50])
            return None
    
    def calculate_similarity(
        self,
        smiles1: str,
        smiles2: str,
        fp_type: str = "morgan",
        metric: str = "tanimoto"
    ) -> Optional[float]:
        """
        두 SMILES 간 유사도 계산
        
        Args:
            smiles1: 첫 번째 SMILES
            smiles2: 두 번째 SMILES
            fp_type: fingerprint 타입
            metric: 유사도 메트릭 (tanimoto, dice, cosine)
        
        Returns:
            유사도 (0.0 ~ 1.0)
        """
        if not self._rdkit_available:
            return None
        
        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem, MACCSkeys
            from rdkit import DataStructs
            
            mol1 = Chem.MolFromSmiles(smiles1)
            mol2 = Chem.MolFromSmiles(smiles2)
            
            if mol1 is None or mol2 is None:
                return None
            
            # Fingerprint 생성
            if fp_type == "morgan":
                fp1 = AllChem.GetMorganFingerprintAsBitVect(mol1, self.DEFAULT_RADIUS, nBits=self.DEFAULT_NBITS)
                fp2 = AllChem.GetMorganFingerprintAsBitVect(mol2, self.DEFAULT_RADIUS, nBits=self.DEFAULT_NBITS)
            elif fp_type == "maccs":
                fp1 = MACCSkeys.GenMACCSKeys(mol1)
                fp2 = MACCSkeys.GenMACCSKeys(mol2)
            else:
                fp1 = Chem.RDKFingerprint(mol1)
                fp2 = Chem.RDKFingerprint(mol2)
            
            # 유사도 계산
            if metric == "tanimoto":
                similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
            elif metric == "dice":
                similarity = DataStructs.DiceSimilarity(fp1, fp2)
            elif metric == "cosine":
                similarity = DataStructs.CosineSimilarity(fp1, fp2)
            else:
                similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
            
            return round(similarity, 4)
            
        except Exception as e:
            self.logger.error("similarity_compute_failed", error=str(e))
            return None
    
    async def search_similar(
        self,
        query_smiles: str,
        top_k: int = None,
        threshold: float = None,
        fp_type: str = "morgan",
        component_type: Optional[str] = None
    ) -> List[SimilarityResult]:
        """
        카탈로그에서 유사 화합물 검색
        
        Args:
            query_smiles: 쿼리 SMILES
            top_k: 반환할 최대 개수
            threshold: 최소 유사도
            fp_type: fingerprint 타입
            component_type: 컴포넌트 타입 필터 (payload, linker 등)
        
        Returns:
            유사도 순으로 정렬된 결과
        """
        if not self._rdkit_available:
            return []
        
        if not self.db:
            self.logger.warning("db_not_configured")
            return []
        
        top_k = top_k or self.DEFAULT_TOP_K
        threshold = threshold or self.DEFAULT_THRESHOLD
        
        try:
            # 카탈로그에서 SMILES가 있는 화합물 조회
            query = self.db.table("component_catalog").select(
                "id, name, smiles, type"
            ).not_.is_("smiles", "null")
            
            if component_type:
                query = query.eq("type", component_type)
            
            result = query.limit(1000).execute()  # 최대 1000개로 제한
            
            if not result.data:
                return []
            
            # 유사도 계산
            similarities = []
            
            for compound in result.data:
                if not compound.get("smiles"):
                    continue
                
                similarity = self.calculate_similarity(
                    query_smiles, 
                    compound["smiles"], 
                    fp_type
                )
                
                if similarity and similarity >= threshold:
                    similarities.append(SimilarityResult(
                        compound_id=str(compound["id"]),
                        name=compound.get("name", "Unknown"),
                        smiles=compound["smiles"],
                        similarity=similarity,
                        fingerprint_type=fp_type
                    ))
            
            # 유사도 순 정렬
            similarities.sort(key=lambda x: x.similarity, reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            self.logger.error("similarity_search_failed", error=str(e))
            return []
    
    def compute_descriptors(self, smiles: str) -> Optional[Dict[str, Any]]:
        """
        SMILES에서 분자 descriptor 계산
        
        Returns:
            분자량, LogP, TPSA, HBD, HBA 등
        """
        if not self._rdkit_available:
            return None
        
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors, rdMolDescriptors
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            
            return {
                "molecular_weight": round(Descriptors.MolWt(mol), 2),
                "exact_mass": round(Descriptors.ExactMolWt(mol), 4),
                "logp": round(Descriptors.MolLogP(mol), 2),
                "tpsa": round(Descriptors.TPSA(mol), 2),
                "hbd": rdMolDescriptors.CalcNumHBD(mol),
                "hba": rdMolDescriptors.CalcNumHBA(mol),
                "rotatable_bonds": rdMolDescriptors.CalcNumRotatableBonds(mol),
                "rings": rdMolDescriptors.CalcNumRings(mol),
                "aromatic_rings": rdMolDescriptors.CalcNumAromaticRings(mol),
                "heavy_atoms": mol.GetNumHeavyAtoms(),
                "fraction_csp3": round(rdMolDescriptors.CalcFractionCSP3(mol), 3),
            }
            
        except Exception as e:
            self.logger.error("descriptor_compute_failed", error=str(e))
            return None


# 편의 함수
def get_fingerprint_service(db_client=None) -> FingerprintService:
    """FingerprintService 인스턴스 반환"""
    return FingerprintService(db_client)
