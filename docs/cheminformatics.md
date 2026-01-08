# Cheminformatics Guide

RDKit 디스크립터 및 화학 정보 처리 파이프라인 문서입니다.

---

## 1. 디스크립터 목록

### 1.1 기본 디스크립터
| 디스크립터 | 설명 | 사용처 |
|---|---|---|
| `MW` | 분자량 (Molecular Weight) | Eng-Fit |
| `LogP` | 지용성 (Partition Coefficient) | Eng-Fit, AggRisk |
| `TPSA` | 극성 표면적 | Eng-Fit |
| `HBD` | 수소결합 공여체 수 | Eng-Fit |
| `HBA` | 수소결합 수용체 수 | Eng-Fit |
| `RotBonds` | 회전 가능 결합 수 | Eng-Fit |

### 1.2 ADC 특화 디스크립터
| 디스크립터 | 설명 | 사용처 |
|---|---|---|
| `DAR` | Drug-Antibody Ratio | Eng-Fit, AggRisk |
| `H_patch` | 소수성 패치 점수 | Eng-Fit, AggRisk |
| `Fingerprint` | Morgan/ECFP4 | 유사도 검색 |

---

## 2. 계산 파이프라인

### 2.1 Precompute Job
```python
# Worker에서 비동기 실행
async def rdkit_precompute_job(component_id: str):
    """
    1. component_catalog에서 SMILES 조회
    2. RDKit 디스크립터 계산
    3. Fingerprint 생성
    4. component_catalog.descriptors 업데이트
    5. status='active'로 변경
    """
```

### 2.2 실패 처리
- 최대 재시도: 3회
- 타임아웃: 60초/컴포넌트
- 실패 시: `status='failed'` + 오류 로그

---

## 3. API 엔드포인트

### 유사도 검색
```http
POST /api/v1/fingerprint/search
Content-Type: application/json

{
  "smiles": "CC(=O)Oc1ccccc1C(=O)O",
  "threshold": 0.7,
  "limit": 10
}
```

### 응답
```json
{
  "query_smiles": "CC(=O)Oc1ccccc1C(=O)O",
  "results": [
    {
      "id": "uuid",
      "name": "Aspirin",
      "similarity": 1.0
    }
  ]
}
```

---

## 4. 설치 요구사항

### Docker (권장)
```dockerfile
FROM continuumio/miniconda3
RUN conda install -c conda-forge rdkit=2023.09
```

### pip (실험적)
```bash
pip install rdkit  # 일부 환경에서 동작
```

---

## 5. 코드 위치

| 파일 | 설명 |
|---|---|
| `services/engine/app/services/fingerprint.py` | Fingerprint 서비스 |
| `services/engine/app/api/fingerprint.py` | API 라우터 |
| `services/worker/jobs/rdkit_precompute.py` | Precompute Job |
