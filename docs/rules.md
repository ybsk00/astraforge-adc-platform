# 룰 엔진 (Rule Engine)

> 본 문서는 ADC 후보 물질 평가에 사용되는 룰 엔진의 YAML 규격과 샘플을 정의합니다.

---

## 1. 개요

룰 엔진은 후보 물질의 **필터링, 경고, 페널티 적용**에 사용됩니다.
도메인 전문가가 정의한 규칙을 YAML로 관리하며, 런 실행 시 배치로 적용됩니다.

---

## 2. 룰 유형

| 유형 | 설명 | 예시 |
|------|------|------|
| `hard_reject` | 즉시 탈락 (조합 생성 제외) | DAR > 8 |
| `soft_reject` | 점수 0, 하지만 기록 유지 | 치명적 독성 시그널 |
| `penalty` | 점수 감점 | LogP > 4.0 → -10점 |
| `alert` | 경고 표시 (점수 무영향) | 주요 장기 발현 |
| `require_protocol` | 특정 프로토콜 필수 지정 | AggRisk 높음 → SEC |

---

## 3. YAML 규격

### 3.1 기본 구조

```yaml
rules:
  - id: "rule_001"
    name: "DAR 과도 하드리젝트"
    version: "1.0"
    enabled: true
    priority: 1  # 낮을수록 먼저 평가
    
    # 적용 대상
    scope:
      phase: ["combination"]  # combination, scoring, evidence
      component_types: ["linker", "payload"]
    
    # 조건
    condition:
      expression: "DAR > 8"
      # 또는 복합 조건
      # all:
      #   - field: "DAR"
      #     operator: ">"
      #     value: 8
      #   - field: "payload_type"
      #     operator: "=="
      #     value: "cytotoxic"
    
    # 액션
    action:
      type: "hard_reject"
      message: "DAR이 8을 초과하여 제외됨"
      
    # 근거 문서 (선택)
    references:
      - type: "internal"
        id: "policy_001"
      - type: "pubmed"
        id: "PMID:12345678"
```

### 3.2 조건 연산자

| 연산자 | 설명 | 예시 |
|--------|------|------|
| `>`, `<`, `>=`, `<=` | 비교 | `LogP > 4.0` |
| `==`, `!=` | 동등 비교 | `status == 'active'` |
| `in`, `not_in` | 포함 여부 | `tissue in ['liver', 'kidney']` |
| `contains` | 문자열 포함 | `name contains 'MMAE'` |
| `is_null`, `is_not_null` | NULL 체크 | `smiles is_not_null` |

### 3.3 복합 조건

```yaml
condition:
  all:  # AND 조건
    - field: "LogP"
      operator: ">"
      value: 4.0
    - field: "DAR"
      operator: ">="
      value: 4
      
# 또는
condition:
  any:  # OR 조건
    - field: "critical_tissue"
      operator: "=="
      value: true
    - field: "OOT_score"
      operator: ">"
      value: 50
```

---

## 4. 샘플 룰셋 (v0.1)

```yaml
# ruleset_v0.1.yaml
version: "0.1"
description: "ADC 플랫폼 초기 룰셋"
created_at: "2026-01-09"
author: "도메인 전문가"

rules:
  # === Hard Reject ===
  - id: "hr_001"
    name: "DAR 과도"
    priority: 1
    condition:
      expression: "DAR > 8"
    action:
      type: "hard_reject"
      message: "DAR > 8: 약동학적 불안정성 위험"

  - id: "hr_002"
    name: "치명적 독성 페이로드"
    priority: 1
    condition:
      expression: "payload_class == 'withdrawn'"
    action:
      type: "hard_reject"
      message: "임상 철회된 페이로드 사용 불가"

  # === Penalty ===
  - id: "pn_001"
    name: "고소수성 페널티"
    priority: 10
    condition:
      expression: "LogP > 4.0"
    action:
      type: "penalty"
      value: 10
      target: "EngFit"
      message: "LogP > 4.0: 응집 위험 증가"

  - id: "pn_002"
    name: "DAR 4 초과 페널티"
    priority: 10
    condition:
      expression: "DAR > 4"
    action:
      type: "penalty"
      value: 5
      target: "EngFit"
      message: "DAR > 4: 생산성 저하 가능"

  # === Alert ===
  - id: "al_001"
    name: "주요 장기 발현 경고"
    priority: 20
    condition:
      expression: "critical_tissue_expression == true"
    action:
      type: "alert"
      severity: "warning"
      message: "심장/간/신장에서 표적 발현 감지"

  - id: "al_002"
    name: "임상 실패 이력"
    priority: 20
    condition:
      expression: "clinical_failure_count > 0"
    action:
      type: "alert"
      severity: "caution"
      message: "동일 표적/페이로드 조합의 임상 실패 이력 존재"

  # === Protocol Requirement ===
  - id: "pr_001"
    name: "고응집 리스크 → SEC 필수"
    priority: 30
    condition:
      expression: "AggRisk > 30"
    action:
      type: "require_protocol"
      template_id: "sec_v1"
      message: "응집 위험 높음: SEC 분석 필수"
```

---

## 5. 룰 적용 순서

```
1. Hard Reject 룰 평가 (priority 1~9)
   → 해당 시 candidate_reject_summaries에 기록, 조합 제외

2. Soft Reject 룰 평가 (priority 10~19)
   → 해당 시 점수 0 설정, 기록 유지

3. Penalty 룰 평가 (priority 10~19)
   → 해당 시 점수 감점, candidate_rule_hits에 기록

4. Alert 룰 평가 (priority 20~29)
   → 해당 시 UI 경고 표시용 플래그 설정

5. Protocol Requirement 룰 평가 (priority 30~)
   → 해당 시 필수 프로토콜 목록에 추가
```

---

## 6. 룰 성능 추적

`rule_performance` 테이블로 룰의 적중률 및 정확도를 모니터링합니다.

```sql
SELECT 
  rule_id,
  COUNT(*) as hit_count,
  AVG(CASE WHEN feedback = 'agree' THEN 1 ELSE 0 END) as accuracy
FROM candidate_rule_hits
LEFT JOIN human_feedback ON ...
GROUP BY rule_id
ORDER BY hit_count DESC;
```

---

## 7. 버전 관리

- 룰셋 파일은 `config/rulesets/` 디렉토리에 저장
- 파일명: `ruleset_v{version}.yaml`
- 변경 시 새 버전 파일 생성 (기존 버전 유지)
- 런 실행 시 사용된 룰셋 버전 기록

---

## 관련 문서

- [scoring.md](./scoring.md) - 스코어링 산식
- [protocol-templates.md](./protocol-templates.md) - 프로토콜 템플릿
- [db.md](./db.md) - 데이터베이스 스키마
