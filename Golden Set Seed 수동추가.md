# Golden Set Seed v1.2 — 20개 수동 DB 적재용 (Anti-Gravity 입력 문서)

작성일: 2026-01-14  
목표: 아래 20개 Seed를 **수동으로 DB에 적재**하고, 이후 Big3 워커(ClinicalTrials / PubChem / ChEMBL)가 **근거·상태·구조(SMILES)·활성 데이터**를 보강할 수 있도록 “정답지(Seed)”를 만든다.

---

## 0) 이번 버전에서 반드시 고칠 점 (중요)
당신이 제공한 Python 전처리에는 아래 리스크가 있습니다.

### A. `fillna('')` 사용 금지 (권장: NULL 유지)
- `df.fillna('')`는 DB에서 **빈 문자열**로 들어가서 나중에 품질검사/NULL 체크가 모두 깨집니다.
- 권장:
  - CSV로 넣을 때는 **빈 칸(Empty)** 으로 남겨서 DB에서 NULL로 들어가게 하거나,
  - JSON Insert라면 `null` 그대로 유지.

### B. outcome_label 표준화 필요
현재 데이터에는 `Success / Fail / Uncertain / Caution`이 섞여 있습니다.  
권장 표준:
- `SUCCESS | FAIL | UNCERTAIN`
- `CAUTION`은 `outcome_label`이 아니라 별도 필드로 분리:
  - `caution_flag: true`
  - `caution_reason: "Ocular toxicity"` 등

이번 문서에서는 **원본을 유지**하되, 아래 “표준화 권장 매핑”을 함께 제공합니다.

---

## 1) 권장 Enum 매핑표 (DB 적재 후 정규화 작업용)
아래는 “Seed 입력값(원본)” → “권장 표준값”입니다.  
(지금 당장 강제하지 않고, Phase 1.5 Resolver/Quality Gate에서 정리해도 됩니다.)

### 1.1 portfolio_group
- `Group A (Approved)` → `A_APPROVED`
- `Group B (Late)` → `B_LATE`
- `Group C (Novelty)` → `C_NOVELTY`
- `Group D (Discontinued)` → `D_DISCONTINUED`

### 1.2 clinical_phase
- `Approved` → `APPROVED`
- `Phase 1/2/3` → `P1/P2/P3`

### 1.3 program_status
- `Active` → `ACTIVE`
- `Terminated` → `TERMINATED`

### 1.4 outcome_label
- `Success` → `SUCCESS`
- `Fail` → `FAIL`
- `Uncertain` → `UNCERTAIN`
- `Caution` → `UNCERTAIN + caution_flag=true`

---

## 2) Seed 20 Items (원본 값 그대로 유지)
아래 20개를 **그대로 DB에 입력**하세요.  
(추후 Quality Gate에서 Enum 표준화/동의어 정리/타겟 표준명(HUGO)로 정제)

---

### Group A (Approved) — 10개

#### A-01 Trastuzumab deruxtecan
- portfolio_group: Group A (Approved)
- drug_name_canonical: Trastuzumab deruxtecan
- aliases: Enhertu|DS-8201
- target: HER2
- antibody: Trastuzumab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: Topo1 inhibitor
- payload_exact_name: DXd
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Approved
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: ILD (Interstitial Lung Disease)
- failure_mode: null
- primary_source_type: FDA Label
- primary_source_id: BLA 761139

#### A-02 Trastuzumab emtansine
- portfolio_group: Group A (Approved)
- drug_name_canonical: Trastuzumab emtansine
- aliases: Kadcyla|T-DM1
- target: HER2
- antibody: Trastuzumab
- linker_family: Non-cleavable
- linker_trigger: N/A
- payload_family: Microtubule inh
- payload_exact_name: DM1 (Maytansinoid)
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Approved
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: Thrombocytopenia
- failure_mode: null
- primary_source_type: FDA Label
- primary_source_id: BLA 125427

#### A-03 Brentuximab vedotin
- portfolio_group: Group A (Approved)
- drug_name_canonical: Brentuximab vedotin
- aliases: Adcetris|SGN-35
- target: CD30
- antibody: Brentuximab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: Microtubule inh
- payload_exact_name: MMAE (Auristatin)
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Approved
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: Peripheral Neuropathy
- failure_mode: null
- primary_source_type: FDA Label
- primary_source_id: BLA 125388

#### A-04 Sacituzumab govitecan
- portfolio_group: Group A (Approved)
- drug_name_canonical: Sacituzumab govitecan
- aliases: Trodelvy|IMMU-132
- target: TROP2
- antibody: Sacituzumab
- linker_family: Cleavable
- linker_trigger: Acid-labile (pH)
- payload_family: Topo1 inhibitor
- payload_exact_name: SN-38
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Approved
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: Severe Diarrhea / Neutropenia
- failure_mode: null
- primary_source_type: FDA Label
- primary_source_id: BLA 761115

#### A-05 Enfortumab vedotin
- portfolio_group: Group A (Approved)
- drug_name_canonical: Enfortumab vedotin
- aliases: Padcev|ASG-22ME
- target: Nectin-4
- antibody: Enfortumab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: Microtubule inh
- payload_exact_name: MMAE (Auristatin)
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Approved
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: Skin reactions (SJS/TEN)
- failure_mode: null
- primary_source_type: FDA Label
- primary_source_id: BLA 761144

#### A-06 Polatuzumab vedotin
- portfolio_group: Group A (Approved)
- drug_name_canonical: Polatuzumab vedotin
- aliases: Polivy
- target: CD79b
- antibody: Polatuzumab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: Microtubule inh
- payload_exact_name: MMAE (Auristatin)
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Approved
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: Peripheral Neuropathy
- failure_mode: null
- primary_source_type: FDA Label
- primary_source_id: BLA 761121

#### A-07 Tisotumab vedotin
- portfolio_group: Group A (Approved)
- drug_name_canonical: Tisotumab vedotin
- aliases: Tivdak
- target: Tissue Factor
- antibody: Tisotumab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: Microtubule inh
- payload_exact_name: MMAE (Auristatin)
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Approved
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: Ocular Toxicity
- failure_mode: null
- primary_source_type: FDA Label
- primary_source_id: BLA 761208

#### A-08 Loncastuximab tesirine
- portfolio_group: Group A (Approved)
- drug_name_canonical: Loncastuximab tesirine
- aliases: Zynlonta|ADCT-402
- target: CD19
- antibody: Loncastuximab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: DNA alkylator
- payload_exact_name: SG3199 (PBD dimer)
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Approved
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: Edema / Effusion
- failure_mode: null
- primary_source_type: FDA Label
- primary_source_id: BLA 761169

#### A-09 Mirvetuximab soravtansine
- portfolio_group: Group A (Approved)
- drug_name_canonical: Mirvetuximab soravtansine
- aliases: Elahere|IMGN853
- target: FR alpha
- antibody: Mirvetuximab
- linker_family: Cleavable
- linker_trigger: Disulfide (Redox)
- payload_family: Microtubule inh
- payload_exact_name: DM4 (Maytansinoid)
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Approved
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: Ocular Toxicity
- failure_mode: null
- primary_source_type: FDA Label
- primary_source_id: BLA 761310

#### A-10 Gemtuzumab ozogamicin
- portfolio_group: Group A (Approved)
- drug_name_canonical: Gemtuzumab ozogamicin
- aliases: Mylotarg
- target: CD33
- antibody: Gemtuzumab
- linker_family: Cleavable
- linker_trigger: Acid-labile (Hydrazone)
- payload_family: DNA breaker
- payload_exact_name: Calicheamicin
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Approved
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: VOD (Veno-occlusive disease)
- failure_mode: null
- primary_source_type: FDA Label
- primary_source_id: BLA 761060

---

### Group B (Late) — 6개

#### B-01 Datopotamab deruxtecan
- portfolio_group: Group B (Late)
- drug_name_canonical: Datopotamab deruxtecan
- aliases: Dato-DXd|DS-1062
- target: TROP2
- antibody: Datopotamab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: Topo1 inhibitor
- payload_exact_name: DXd
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Phase 3
- program_status: Active
- outcome_label: Uncertain
- key_risk_category: Toxicity
- key_risk_signal: Stomatitis / Mucositis
- failure_mode: null
- primary_source_type: Clinical Trial
- primary_source_id: NCT04656652

#### B-02 Patritumab deruxtecan
- portfolio_group: Group B (Late)
- drug_name_canonical: Patritumab deruxtecan
- aliases: HER3-DXd|U3-1402
- target: HER3
- antibody: Patritumab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: Topo1 inhibitor
- payload_exact_name: DXd
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Phase 3
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: Thrombocytopenia
- failure_mode: null
- primary_source_type: Clinical Trial
- primary_source_id: NCT04619004

#### B-03 Sacituzumab tirumotecan (MK-2870|SKB264)
- portfolio_group: Group B (Late)
- drug_name_canonical: Sacituzumab tirumotecan
- aliases: MK-2870|SKB264
- target: TROP2
- antibody: Sacituzumab
- linker_family: Cleavable
- linker_trigger: Hydrolysable (Sulfonyl)
- payload_family: Topo1 inhibitor
- payload_exact_name: Belotecan derivative
- proxy_smiles_flag: true
- proxy_reference: Belotecan core
- clinical_phase: Phase 3
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: Hematologic Toxicity
- failure_mode: null
- primary_source_type: Review Paper
- primary_source_id: PMID: 38245678

#### B-04 Telisotuzumab vedotin (ABBV-399)
- portfolio_group: Group B (Late)
- drug_name_canonical: Telisotuzumab vedotin
- aliases: Teliso-V|ABBV-399
- target: c-Met
- antibody: Telisotuzumab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: Microtubule inh
- payload_exact_name: MMAE (Auristatin)
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Phase 3
- program_status: Active
- outcome_label: Success
- key_risk_category: Toxicity
- key_risk_signal: Neuropathy
- failure_mode: null
- primary_source_type: Clinical Trial
- primary_source_id: NCT05029882

#### B-05 Abbv-400 (ABBV-400)
- portfolio_group: Group B (Late)
- drug_name_canonical: Abbv-400
- aliases: ABBV-400
- target: c-Met
- antibody: AbbVie mAb
- linker_family: Cleavable
- linker_trigger: Protease (Top1 linker)
- payload_family: Topo1 inhibitor
- payload_exact_name: Top1i novel
- proxy_smiles_flag: true
- proxy_reference: SN-38 core
- clinical_phase: Phase 2
- program_status: Active
- outcome_label: Uncertain
- key_risk_category: Toxicity
- key_risk_signal: Anemia
- failure_mode: null
- primary_source_type: Clinical Trial
- primary_source_id: NCT06084481

#### B-06 Trastuzumab duocarmazine (SYD985)
- portfolio_group: Group B (Late)
- drug_name_canonical: Trastuzumab duocarmazine
- aliases: SYD985
- target: HER2
- antibody: Trastuzumab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: DNA alkylator
- payload_exact_name: Duocarmycin
- proxy_smiles_flag: true
- proxy_reference: Seco-DUBA
- clinical_phase: Phase 3
- program_status: Active
- outcome_label: Caution
- key_risk_category: Toxicity
- key_risk_signal: Ocular Toxicity
- failure_mode: null
- primary_source_type: Review Paper
- primary_source_id: PMID: 37185211

---

### Group C (Novelty) — 2개

#### C-01 BL-B01D1 (EGFRxHER3 ADC)
- portfolio_group: Group C (Novelty)
- drug_name_canonical: BL-B01D1
- aliases: BL-B01D1|EGFRxHER3 ADC
- target: EGFR / HER3
- antibody: Bispecific mAb
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: Topo1 inhibitor
- payload_exact_name: Ed-04 (Exatecan deriv)
- proxy_smiles_flag: true
- proxy_reference: Exatecan core
- clinical_phase: Phase 3
- program_status: Active
- outcome_label: Success
- key_risk_category: CMC
- key_risk_signal: Bispecific Manufacturing Complexity
- failure_mode: null
- primary_source_type: Clinical Trial
- primary_source_id: NCT05983488

#### C-02 Farletuzumab ecteribulin (MORAb-202)
- portfolio_group: Group C (Novelty)
- drug_name_canonical: Farletuzumab ecteribulin
- aliases: MORAb-202
- target: FR alpha
- antibody: Farletuzumab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: Microtubule inh
- payload_exact_name: Eribulin
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Phase 2
- program_status: Active
- outcome_label: Success
- key_risk_category: Efficacy
- key_risk_signal: Lung Toxicity (Low grade)
- failure_mode: null
- primary_source_type: Review Paper
- primary_source_id: PMID: 38814723

---

### Group D (Discontinued) — 2개

#### D-01 Rovalpituzumab tesirine (Rova-T)
- portfolio_group: Group D (Discontinued)
- drug_name_canonical: Rovalpituzumab tesirine
- aliases: Rova-T|SC16LD6.5
- target: DLL3
- antibody: Rovalpituzumab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: DNA alkylator
- payload_exact_name: Tesirine (PBD dimer)
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Phase 3
- program_status: Terminated
- outcome_label: Fail
- key_risk_category: Toxicity
- key_risk_signal: Severe Effusion / Sepsis
- failure_mode: Toxicity
- primary_source_type: Clinical Trial
- primary_source_id: NCT01901653

#### D-02 Vadastuximab talirine (SGN-CD33A)
- portfolio_group: Group D (Discontinued)
- drug_name_canonical: Vadastuximab talirine
- aliases: SGN-CD33A
- target: CD33
- antibody: Vadastuximab
- linker_family: Cleavable
- linker_trigger: Protease (Cathepsin)
- payload_family: DNA alkylator
- payload_exact_name: PBD dimer (SGD-1882)
- proxy_smiles_flag: false
- proxy_reference: null
- clinical_phase: Phase 3
- program_status: Terminated
- outcome_label: Fail
- key_risk_category: Safety
- key_risk_signal: Patient Death (AML)
- failure_mode: Safety
- primary_source_type: Clinical Trial
- primary_source_id: NCT02785900

---

## 3) DB 적재 체크리스트
- [ ] NULL을 빈 문자열로 대체하지 않았는가? (특히 proxy_reference, failure_mode)
- [ ] `outcome_label="Caution"` 항목은 추후 `caution_flag/caution_reason`로 분리할 계획이 있는가?
- [ ] target 표준명(예: Tissue Factor → F3, FR alpha → FOLR1, c-Met → MET)을 Resolver에서 처리할 준비가 되었는가?
- [ ] `proxy_smiles_flag=true` 항목은 PubChem 매핑 실패 시 “Proxy 구조”로 RDKit 계산 대상임을 분명히 마킹했는가?

---

## 4) 다음 자동화(워커) 연결 포인트
- ClinicalTrials.gov: `primary_source_id`가 NCT인 항목은 “상태/Phase/중단사유” 자동 갱신
- PubChem: `payload_exact_name`, `proxy_reference`를 기반으로 SMILES 확보 (실패 시 관리자 보정)
- ChEMBL: target(표준화 후) 기반 bioactivity/Mechanism 보강

---
