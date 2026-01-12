# component_catalog에 Target 200개 시딩 전략 (초기 리스트 + 확장 방법)
목표: 현재 HPA/UniProt/OpenTargets 커넥터가 기본값(5개 gene_symbols)만 돌면서 `fetched: 3~5` 수준으로 끝나는 문제를 해결하기 위해, **component_catalog(target) 200개를 먼저 채우고(batch_mode 기반)** 이후 커넥터들이 “대량 동기화”되도록 만든다.

---

## 0) 핵심 결론 (왜 지금 1개/0개/2개만 업데이트되나?)
현재 HPA/UniProt/OpenTargets/HPA는 **seed에 gene_symbols/ensembl_ids/uniprot_ids가 없으면 기본값(5개)**만 동기화합니다.  
따라서 DB에 target이 거의 없거나, seed가 기본값이면 `fetched`가 작게 나오는 것이 정상입니다.

해결 방향은 1가지입니다.

- **Step 1:** component_catalog에 target을 최소 200개 넣는다.
- **Step 2:** UniProt/HPA/OpenTargets를 **batch_mode**로 실행해 catalog의 target들을 기준으로 대량 동기화한다.
- **Step 3:** 이후 “Golden Seed(ADC100)” 같은 작업이 target pool을 충분히 참조할 수 있게 만든다.

---

## 1) 데이터 모델 가정 (component_catalog의 target에 넣을 최소 필드)
현재 seed_job.py를 기준으로 target은 다음 필드가 중요합니다.

- type: `"target"`
- name: `"HER2"` 같은 표적 명칭(표준)
- gene_symbol: `"ERBB2"`
- uniprot_accession: `"P04626"` (가능하면 함께)
- ensembl_gene_id: `"ENSG..."`
- is_gold: boolean
- is_active: boolean
- quality_grade: `"gold"` / `"silver"` / `"bronze"` (권장)
- workspace_id: NULL (시스템 공용)

> “정답” 수준이 아니라도 됩니다. 초기 200개는 **커넥터 확장을 위한 seed pool**입니다.
> 이후 Resolve IDs 커넥터로 uniprot/ensembl을 보강할 수 있습니다.

---

## 2) 시딩 전략: “3단계로 200개” 만드는 방식 (가장 현실적인 최적안)

### 2.1 Phase A (즉시): Gold 20~30개 (수동 고정 리스트)
- HER2, TROP2, Nectin-4, EGFR, MET, CD19, CD20, CD22, CD30, CD33, BCMA, DLL3, LIV1(SLC39A6), Mesothelin(MSLN), PSMA(FOLH1), Claudin18.2(CLDN18), HER3(ERBB3), TF(F3), CEACAM5, CD79b 등
- 이 구간은 “이름/심볼 표준”이 매우 중요하므로 최소한만 “확실하게” 넣습니다.

### 2.2 Phase B (확장): ADC/항체 표적 후보 100개 (리스트 기반, gene_symbol 중심)
- 이 구간은 uniprot_accession/ensembl_gene_id를 **처음엔 비워도 됩니다.**
- 우선 `name` + `gene_symbol`만 채워도 batch_mode 검색에 유효합니다.
- 이후 Resolve IDs 또는 UniProt 동기화로 보강합니다.

### 2.3 Phase C (롱테일): 암/세포표면 단백질 70~100개
- “세포막/세포표면/암 관련” 유전자 심볼을 대량으로 넣습니다.
- HPA/OpenTargets를 돌리면 자동으로 프로파일이 채워집니다.

> 핵심은 **“완벽한 200개”가 아니라 “작동하는 200개”**입니다.

---

## 3) 추천 구현 방식 2가지 (택1)
아래 중 **A안(파일 기반 일괄 시딩)**이 가장 빠르고 안정적입니다.

### A안) CSV/JSON 파일로 200개 준비 → seed_job에서 파일 읽어 insert
- 장점: 재현성 최고, 운영에서 계속 사용 가능
- 단점: 파일을 먼저 만들어야 함

### B안) SQL로 200개 INSERT (최초 1회)
- 장점: 즉시 실행 가능
- 단점: 관리/확장/버전관리 어려움

권장: **A안**

---

## 4) A안 상세: targets_seed_200.json 생성 + worker seed_job 확장

### 4.1 파일 위치
`services/worker/seeds/targets_seed_200.json`

### 4.2 JSON 포맷 (예시)
```json
[
  {
    "name": "HER2",
    "gene_symbol": "ERBB2",
    "uniprot_accession": "P04626",
    "ensembl_gene_id": "ENSG00000141736",
    "quality_grade": "gold"
  },
  {
    "name": "HER3",
    "gene_symbol": "ERBB3",
    "uniprot_accession": "P21860",
    "ensembl_gene_id": "ENSG00000065361",
    "quality_grade": "gold"
  },
  {
    "name": "TROP2",
    "gene_symbol": "TACSTD2",
    "quality_grade": "gold"
  }
]
4.3 seed_job.py 수정 포인트 (개념)
기존 GOLD_TARGETS 외에, 파일이 존재하면 그 데이터를 읽어서 추가 시딩

upsert 기준: (type, name, workspace_id NULL) 또는 (type, gene_symbol, workspace_id NULL) 중 하나로 정규화

name/gene_symbol 둘 다 들어오면: name 우선, 없으면 gene_symbol로 name을 채우는 fallback

의사코드:

python
코드 복사
# seed_job.py 내부
targets = GOLD_TARGETS + load_json_if_exists("seeds/targets_seed_200.json")

for t in targets:
  data = {
    "type": "target",
    "name": t["name"],
    "gene_symbol": t.get("gene_symbol"),
    "uniprot_accession": t.get("uniprot_accession"),
    "ensembl_gene_id": t.get("ensembl_gene_id"),
    "is_gold": (t.get("quality_grade") == "gold"),
    "is_active": True,
    "quality_grade": t.get("quality_grade", "silver")
  }
  # 기존 로직대로 select 후 insert/update
5) “초기 리스트(샘플)” — 지금 당장 넣을 30개 (Phase A)
아래는 ADC/항체약물에서 자주 등장하는 표적들입니다.
(처음엔 gene_symbol만으로도 충분. uniprot/ensembl은 추후 보강 가능)

HER2 (ERBB2)

HER3 (ERBB3)

TROP2 (TACSTD2)

Nectin-4 (NECTIN4)

EGFR (EGFR)

MET (MET)

MSLN (MSLN)

PSMA (FOLH1)

CLDN18 (CLDN18) # Claudin 18.2는 CLDN18 isoform 이슈, 추후 보강

LIV1 (SLC39A6)

CD19 (CD19)

CD20 (MS4A1)

CD22 (CD22)

CD30 (TNFRSF8)

CD33 (CD33)

CD79B (CD79B)

BCMA (TNFRSF17)

DLL3 (DLL3)

TF (F3)

CEACAM5 (CEACAM5)

MUC1 (MUC1)

EPCAM (EPCAM)

FGFR2 (FGFR2)

FGFR3 (FGFR3)

PD-L1 (CD274)

PD-1 (PDCD1)

B7-H3 (CD276)

IL3RA (IL3RA) # CD123

SLAMF7 (SLAMF7)

GPNMB (GPNMB)

Phase B/C에서 200개로 확장합니다. “너무 정확해야 한다”는 부담을 가지면 끝까지 못 갑니다.
먼저 200개를 채워 batch_mode 파이프라인을 돌릴 수 있게 만드는 것이 1차 목표입니다.

6) 실행 순서 (바로 해야 하는 순서)
Seed Data 커넥터 실행

component_catalog에 target 200개가 들어가야 함

Resolve IDs 커넥터 실행

gene_symbol 중심으로 uniprot/ensembl 매핑 보강(가능한 범위)

UniProt 커넥터 batch_mode 실행

component_catalog의 uniprot_accession 기반으로 target_profiles 채움

OpenTargets 커넥터 실행

disease association/priority 등 enrichment

HPA 커넥터 실행

발현/조직 정보 enrichment

7) 검증 SQL (200개가 제대로 들어갔는지)
sql
코드 복사
-- target이 몇 개인지
select count(*) 
from component_catalog 
where type='target' and workspace_id is null;

-- gene_symbol 누락률
select 
  count(*) filter (where gene_symbol is null) as missing_gene_symbol,
  count(*) as total
from component_catalog
where type='target' and workspace_id is null;

-- 상위 20개 샘플 확인
select id, name, gene_symbol, uniprot_accession, ensembl_gene_id, quality_grade
from component_catalog
where type='target' and workspace_id is null
order by created_at desc
limit 20;
8) 운영 관점 권장 규칙 (중복/표준화)
name은 “표적명(관용명)”으로, gene_symbol은 표준 심볼로 유지

중복 제거 기준:

1차: gene_symbol 동일하면 동일 타겟으로 간주

2차: gene_symbol이 없으면 name으로만 비교

신규 입력 시:

gene_symbol이 들어오면 name이 약간 달라도 gene_symbol 기준으로 merge

9) 다음 액션 (당장 해야 할 것)
(1) targets_seed_200.json을 만들어서 worker에 포함

(2) Seed Data 커넥터 실행 → component_catalog target이 200개인지 확인

(3) UniProt/HPA/OpenTargets를 batch_mode로 돌리도록 config/seed를 바꾸기