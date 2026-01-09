# 프로토콜 템플릿 (Protocol Templates)

> 본 문서는 ADC 후보 물질 개발 과정에서 필요한 실험 프로토콜 템플릿을 정의합니다.

---

## 1. 개요

ADC 개발 과정에서 각 리스크 요소에 따라 수행해야 하는 실험 프로토콜을 표준화합니다.
룰 엔진과 연동하여 특정 리스크가 감지되면 해당 프로토콜을 자동으로 추천합니다.

---

## 2. 초기 템플릿 목록 (MVP)

### 2.1 SEC (Size Exclusion Chromatography)

**목적:** 응집(Aggregation) 확인

| 항목 | 내용 |
|------|------|
| 트리거 조건 | `AggRisk > 30` 또는 `LogP > 3.5` |
| 샘플 요구량 | 100 μg |
| 분석 시간 | 2-4시간 |
| 결과 지표 | 단량체 비율 (%), HMW species (%) |
| 합격 기준 | 단량체 ≥ 95%, HMW ≤ 2% |

### 2.2 HIC (Hydrophobic Interaction Chromatography)

**목적:** 소수성 프로파일 분석

| 항목 | 내용 |
|------|------|
| 트리거 조건 | `H_patch > 50` 또는 `LogP > 4.0` |
| 샘플 요구량 | 50 μg |
| 분석 시간 | 1-2시간 |
| 결과 지표 | 체류 시간 (min), 피크 형태 |
| 합격 기준 | 단일 대칭 피크, 체류 시간 < 15분 |

### 2.3 Plasma Stability + Free Drug LC-MS

**목적:** 혈장 안정성 및 유리 약물 분석

| 항목 | 내용 |
|------|------|
| 트리거 조건 | `CLV > 40` (cleavage risk) |
| 샘플 요구량 | 200 μg |
| 분석 시간 | 24-72시간 (인큐베이션) |
| 결과 지표 | 잔존율 (%), 유리 약물 농도 |
| 합격 기준 | 24h 잔존율 ≥ 80%, 유리 약물 < 5% |

### 2.4 Internalization Kinetics

**목적:** 세포 내재화 속도 측정

| 항목 | 내용 |
|------|------|
| 트리거 조건 | `INT < 50` (낮은 내재화 점수) |
| 샘플 요구량 | 500 μg |
| 분석 시간 | 4-24시간 |
| 결과 지표 | 내재화 반감기 (t½), 최대 내재화율 |
| 합격 기준 | t½ < 2h, 최대 내재화율 ≥ 70% |

### 2.5 Cytotoxicity Panel

**목적:** 표적 발현 세포주 활성 테스트

| 항목 | 내용 |
|------|------|
| 트리거 조건 | 모든 후보 (필수) |
| 샘플 요구량 | 1 mg |
| 분석 시간 | 72-96시간 |
| 결과 지표 | IC50, 선택성 지수 (SI) |
| 합격 기준 | IC50 < 1 nM (표적 양성), SI > 100 |

---

## 3. 템플릿 저장 정책

### 3.1 저장 방식 (MVP)

```
/config/protocol-templates/
├── sec.yaml
├── hic.yaml
├── plasma-stability.yaml
├── internalization.yaml
└── cytotoxicity.yaml
```

- **초기:** 코드/YAML 기반 (Git 버전 관리)
- **확장:** `protocol_templates` DB 테이블 (운영 UI 필요 시)

### 3.2 YAML 템플릿 예시

```yaml
id: "sec_v1"
name: "Size Exclusion Chromatography"
version: "1.0"
category: "aggregation"

trigger:
  conditions:
    - field: "AggRisk"
      operator: ">"
      value: 30
    - field: "LogP"
      operator: ">"
      value: 3.5
  logic: "OR"

requirements:
  sample_amount: "100 μg"
  lead_time: "2-4 hours"
  equipment: ["SEC column", "HPLC system"]

outputs:
  - name: "monomer_ratio"
    unit: "%"
    acceptance: ">= 95"
  - name: "hmw_species"
    unit: "%"
    acceptance: "<= 2"
```

---

## 4. 룰 연결 정책

| 리스크 유형 | 임계값 | 필수 프로토콜 |
|-------------|--------|---------------|
| AggRisk 높음 | > 30 | SEC |
| LogP 높음 | > 4.0 | HIC |
| Cleavage Risk | > 40 | Plasma Stability |
| 낮은 내재화 | INT < 50 | Internalization |
| 모든 후보 | - | Cytotoxicity Panel |

---

## 5. 버전 관리

- 템플릿 변경 시 `version` 필드 업데이트
- 런 실행 시 사용된 템플릿 버전 기록 (`candidate_protocols.template_version`)
- 주요 변경 사항은 CHANGELOG에 기록

---

## 관련 문서

- [rules.md](./rules.md) - 룰 엔진 규격
- [scoring.md](./scoring.md) - 스코어링 산식
- [evidence.md](./evidence.md) - Evidence Engine 규격
