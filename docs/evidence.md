# Evidence Engine 가이드

문헌 기반 근거 검색 및 검증 시스템 문서입니다.

---

## 1. 아키텍처

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Literature │────▶│   Chunking  │────▶│  Embedding  │
│  Connector  │     │   (300-800) │     │  (OpenAI)   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │   pgvector  │
                                        │   (Index)   │
                                        └──────┬──────┘
                                               │
┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
│   Forced    │◀────│   Hybrid    │◀────│   RAG       │
│   Evidence  │     │   Search    │     │   Query     │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## 2. 핵심 기능

### 2.1 Hybrid Search
- **Semantic**: pgvector 코사인 유사도
- **Keyword**: PostgreSQL FTS (Full Text Search)
- **결합**: RRF (Reciprocal Rank Fusion)

### 2.2 Forced Evidence 규격
모든 주장에 인용이 필요:
```json
{
  "claim": "HER2 is overexpressed in 20% of breast cancers",
  "citations": ["PMID:12345678"],
  "confidence": 0.95
}
```

인용 없으면 "Assumption" 라벨:
```json
{
  "claim": "Expected to have low aggregation",
  "label": "Assumption",
  "confidence": 0.3
}
```

### 2.3 Conflict Alert
충돌 조건:
- 동일 주제에 찬/반 근거 동시 존재
- 인용 수 < 2 + 불확실성 높음
- 실험 조건 불일치

---

## 3. Polarity 태깅

### 3.1 분류
| Polarity | 설명 | 예시 |
|---|---|---|
| `positive` | 긍정적 결과 | 효능 입증, 안정성 확인 |
| `negative` | 부정적 결과 | 독성 발견, 실패 사례 |
| `neutral` | 중립적 정보 | 방법론, 배경 설명 |

### 3.2 Risk-First Retrieval
위험 평가 시 `negative` polarity 우선 검색:
```python
# evidence_signals.polarity = 'negative' 가중치 부스팅
WHERE polarity = 'negative' OR signal_type = 'toxicity'
```

---

## 4. API 엔드포인트

### Evidence 조회
```http
GET /api/v1/design/runs/{run_id}/candidates/{candidate_id}/evidence
```

### 응답
```json
{
  "evidence": [
    {
      "claim": "...",
      "citations": ["PMID:..."],
      "polarity": "positive",
      "confidence": 0.9
    }
  ],
  "conflicts": [
    {
      "topic": "aggregation risk",
      "sources": ["PMID:111", "PMID:222"]
    }
  ]
}
```

---

## 5. 테이블 구조

### literature_documents
| 컬럼 | 설명 |
|---|---|
| `pmid` | PubMed ID |
| `title` | 제목 |
| `abstract` | 초록 |
| `full_text` | 전문 (옵션) |

### literature_chunks
| 컬럼 | 설명 |
|---|---|
| `content` | 청크 텍스트 |
| `embedding` | vector(1536) |
| `polarity` | positive/negative/neutral |

### evidence_signals
| 컬럼 | 설명 |
|---|---|
| `polarity` | 분류 결과 |
| `signal_type` | efficacy/toxicity/stability |
| `confidence` | 신뢰도 (0~1) |

---

## 5. 엔티티 레벨 근거 (v2)

링커 및 페이로드 엔티티의 품질 검수를 위해 별도의 근거 시스템을 운영합니다.

### 5.1 데이터 모델
- **`evidence_snippets`**: 문헌에서 추출된 엔티티 관련 원문 조각.
- **`entity_evidence_map`**: 특정 링커/페이로드와 근거 스니펫 간의 연결.

### 5.2 RAG 연동 전략
1. **추출**: 문헌 수집 시 LLM을 사용하여 링커/페이로드 언급 및 관련 특성(Cleavage, Mechanism 등) 추출.
2. **저장**: 추출된 텍스트를 `evidence_snippets`에 저장하고 해당 엔티티와 매핑.
3. **검수**: 관리자가 검수 큐에서 해당 근거를 확인하고 엔티티 정보를 확정.

---

## 6. 코드 위치

| 파일 | 설명 |
|---|---|
| `services/engine/app/services/evidence.py` | Evidence RAG 서비스 |
| `services/engine/app/services/literature.py` | 문헌 처리 서비스 |
| `services/worker/jobs/literature_ingest.py` | 문헌 수집 Job |
| `apps/frontend/src/lib/actions/admin.ts` | 관리자 검수 및 근거 연동 서버 액션 |
