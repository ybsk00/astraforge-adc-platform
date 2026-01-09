# 스코어링 (Scoring)

> 본 문서는 ADC 후보 물질의 점수 산출 방식과 파라미터 버전 관리 정책을 정의합니다.

---

## 1. 개요

ADC 후보 물질은 4가지 축으로 평가됩니다:

| 점수 | 설명 | 범위 |
|------|------|------|
| **Eng-Fit** | 엔지니어링/개발성 적합도 | 0-100 |
| **Bio-Fit** | 생물학적 적합도 | 0-100 |
| **Safety-Fit** | 안전성 적합도 | 0-100 |
| **Composite** | 가중 합산 점수 | 0-100 |

모든 산식은 `Score = 100 - Risk` 구조를 따릅니다.

---

## 2. Eng-Fit (엔지니어링 적합도) v0.2

### 2.1 산식

```
EngFit = 100 - CMC_Risk

CMC_Risk = clip(
    w_agg * AggRisk
  + w_proc * ProcRisk
  + w_anal * AnalRisk
  + w_unc * UncPenalty
  , 0, 100)
```

### 2.2 용어 정의

| 용어 | 정의 | 계산 방식 |
|------|------|----------|
| **AggRisk** | 응집 위험 | `clip(ω_logP × max(0, LogP - 2.0) + ω_DAR × max(0, DAR - 4.0) + ω_patch × H_patch, 0, 100)` |
| **ProcRisk** | 공정 복잡도 | 룰/태그 기반 (site-specific 여부, 정제 난이도) |
| **AnalRisk** | 분석 난이도 | 룰/태그 기반 (DAR 분포, 응집 분석 요구) |
| **UncPenalty** | 불확실성 페널티 | 필수 피처 결측 시 가산 |

### 2.3 디폴트 가중치 (v0.2)

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| `w_agg` | 0.4 | 응집 위험 가중치 |
| `w_proc` | 0.25 | 공정 복잡도 가중치 |
| `w_anal` | 0.2 | 분석 난이도 가중치 |
| `w_unc` | 0.15 | 불확실성 가중치 |
| `ω_logP` | 10 | LogP 계수 |
| `ω_DAR` | 8 | DAR 계수 |
| `ω_patch` | 0.5 | 소수성 패치 계수 |

---

## 3. Bio-Fit (생물학적 적합도) v0.2

### 3.1 산식

```
BioFit = 100 - BioRisk

BioRisk = clip(
    w_dea × (100 - DEA)
  + w_int × max(0, Int_threshold - INT)
  + w_het × HET_pen
  + w_acc × ACC_pen
  + w_bs × (100 - BS_match)
  , 0, 100)
```

### 3.2 용어 정의

| 용어 | 정의 | 계산 방식 |
|------|------|----------|
| **DEA** | 차별 발현 적합도 | `clip(50 + k_dea × (log2(T_expr_tumor+1) - log2(N_expr_max+1)), 0, 100)` |
| **INT** | 내재화 점수 | `100 × internalization(0~1)` |
| **HET_pen** | 이질성 페널티 | `100 × heterogeneity(0~1)` |
| **ACC_pen** | 접근성 페널티 | `100 × (1 - accessibility)(0~1)` |
| **BS_match** | Bystander 적합도 | `100 × (1 - abs(bystander_need - bystander_capability))` |

### 3.3 디폴트 가중치 (v0.2)

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| `w_dea` | 0.3 | 차별 발현 가중치 |
| `w_int` | 0.25 | 내재화 가중치 |
| `w_het` | 0.15 | 이질성 가중치 |
| `w_acc` | 0.15 | 접근성 가중치 |
| `w_bs` | 0.15 | Bystander 가중치 |
| `Int_threshold` | 50 | 내재화 임계값 |
| `k_dea` | 10 | DEA 스케일링 계수 |

---

## 4. Safety-Fit (안전성 적합도) v0.2

### 4.1 산식

```
SafetyFit = 100 - SafetyRisk

SafetyRisk = clip(
    w_oot × OOT
  + w_haz × PH
  + w_clv × CLV
  + w_sar × SAR
  + w_neg × NEG
  , 0, 100)
```

### 4.2 용어 정의

| 용어 | 정의 | 계산 방식 |
|------|------|----------|
| **OOT** | Off-Target 위험 | `clip(k_oot × log2(N_expr_max+1) + k_crit × critical_tissue_flag, 0, 100)` |
| **PH** | 페이로드 위험도 | `100 × payload_hazard(0~1)` |
| **CLV** | 조기 절단 위험 | `100 × cleavage_risk(0~1)` |
| **SAR** | 전신 노출 위험 | Eng-Fit의 노출/응집 proxy 재사용 |
| **NEG** | 부정 시그널 | `100 × negative_signal(0~1)` (독성/중단 시그널) |

### 4.3 디폴트 가중치 (v0.2)

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| `w_oot` | 0.25 | Off-Target 가중치 |
| `w_haz` | 0.25 | 페이로드 위험 가중치 |
| `w_clv` | 0.2 | 조기 절단 가중치 |
| `w_sar` | 0.15 | 전신 노출 가중치 |
| `w_neg` | 0.15 | 부정 시그널 가중치 |
| `k_oot` | 5 | OOT 스케일링 계수 |
| `k_crit` | 30 | 주요 장기 플래그 가산 |

---

## 5. Composite Score

```
Composite = (
    w_eng × EngFit
  + w_bio × BioFit
  + w_safety × SafetyFit
) / (w_eng + w_bio + w_safety)
```

**디폴트 가중치:** `w_eng = 0.3`, `w_bio = 0.4`, `w_safety = 0.3`

---

## 6. 데이터 저장

### 6.1 score_components

각 후보의 점수 term별 분해값을 저장합니다.

```json
{
  "eng_fit": {
    "AggRisk": 25.5,
    "ProcRisk": 10.0,
    "AnalRisk": 5.0,
    "UncPenalty": 0.0,
    "CMC_Risk": 40.5,
    "final": 59.5
  },
  "bio_fit": { ... },
  "safety_fit": { ... }
}
```

### 6.2 feature_importance

각 term의 기여도를 저장합니다 (SHAP 또는 단순 비율).

```json
{
  "eng_fit": {
    "LogP": 0.35,
    "DAR": 0.25,
    "H_patch": 0.15,
    "ProcRisk": 0.15,
    "AnalRisk": 0.10
  }
}
```

---

## 7. 파라미터 버전 관리

### 7.1 scoring_params 테이블

```sql
CREATE TABLE scoring_params (
  id UUID PRIMARY KEY,
  version VARCHAR(20) NOT NULL UNIQUE,  -- "v0.2"
  params JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES users(id),
  description TEXT,
  is_active BOOLEAN DEFAULT false
);
```

### 7.2 버전 관리 정책

1. **런 실행 시 버전 고정**
   - `design_runs.scoring_version`에 사용된 버전 기록
   - 동일 런은 항상 동일 파라미터로 재현 가능

2. **변경 시 새 버전 생성**
   - 기존 버전 수정 금지
   - 새 버전 활성화 전 Golden Set 검증 필수

3. **승인 절차**
   - 파라미터 변경 → Golden Set 테스트 → 편차 리포트 → 승인 → 활성화

### 7.3 Golden Set 검증

```python
def validate_scoring_params(new_version: str, golden_set: List[Dict]):
    """
    Golden Set으로 새 파라미터 검증
    - 점수 편차 10% 초과 시 경고
    - 순위 변동 20% 초과 시 승인 필요
    """
    results = []
    for case in golden_set:
        old_score = calculate_score(case, current_version)
        new_score = calculate_score(case, new_version)
        deviation = abs(new_score - old_score) / old_score * 100
        results.append({
            "case_id": case["id"],
            "old_score": old_score,
            "new_score": new_score,
            "deviation_pct": deviation
        })
    return results
```

---

## 관련 문서

- [rules.md](./rules.md) - 룰 엔진 규격
- [protocol-templates.md](./protocol-templates.md) - 프로토콜 템플릿
- [cheminformatics.md](./cheminformatics.md) - RDKit 디스크립터
