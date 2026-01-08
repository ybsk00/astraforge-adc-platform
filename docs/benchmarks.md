# 성능 벤치마크 (Benchmarks)

ADC 플랫폼 성능 기준 및 측정 방법입니다.

---

## 1. 성능 목표 (SLA)

### 1.1 후보 생성 파이프라인
| 단계 | 목표 (10K 후보) | 측정 방법 |
|---|---|---|
| 조합 생성 + 하드리젝트 | ≤ 10초 | `run_progress.phase='generating'` |
| 벡터화 스코어 계산 | ≤ 30초 | `run_progress.phase='scoring'` |
| 파레토 프론트 계산 | ≤ 5초 | `run_progress.phase='pareto'` |
| Evidence RAG (Top-50) | ≤ 60초 | `run_progress.phase='evidence'` |
| Protocol 생성 (Top-50) | ≤ 30초 | `run_progress.phase='protocol'` |
| **전체** | **≤ 120초** | run 생성 → 완료 |

### 1.2 문헌 검색
| 쿼리 유형 | P95 목표 |
|---|---|
| Evidence Lookup | ≤ 1.0초 |
| Semantic Search | ≤ 2.0초 |
| Hybrid Search | ≤ 2.5초 |

---

## 2. 측정 방법

### 2.1 파이프라인 성능
```python
# run_progress 테이블에서 측정
SELECT 
    phase,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_seconds,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))) as p95
FROM run_progress
WHERE completed_at IS NOT NULL
GROUP BY phase;
```

### 2.2 API 레이턴시
```bash
# Artillery 또는 k6 사용
k6 run --vus 10 --duration 30s load_test.js
```

---

## 3. 최적화 가이드

### 3.1 조합 생성
- Generator 패턴 사용 (메모리 효율)
- 배치 크기: 500개 권장
- Hard reject 조기 적용

### 3.2 스코어 계산
- NumPy 벡터화 연산 필수
- 루프 금지
- SIMD 활용

### 3.3 Database
- 적절한 인덱스 생성
- pgvector HNSW 인덱스 사용
- Connection pooling (PgBouncer)

---

## 4. 현재 측정 결과

> 측정 환경: VM 4vCPU, 8GB RAM, SSD

| 항목 | 결과 | 상태 |
|---|---|---|
| 10K 후보 파이프라인 | - | 미측정 |
| Evidence P95 | - | 미측정 |
| Semantic Search P95 | - | 미측정 |

> 실 운영 후 업데이트 예정
