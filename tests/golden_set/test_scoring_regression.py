"""
Golden Set Scoring Regression Tests

이 테스트는 scoring_params 변경 시 산식 결과가
예상 범위 내에서 유지되는지 검증합니다.

실행: pytest tests/golden_set/test_scoring_regression.py -v
"""
import pytest
import yaml
import os
from pathlib import Path


# 프로젝트 루트 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "scoring_params_v0.2.yaml"
GOLDEN_SET_PATH = Path(__file__).parent / "golden_cases.yaml"


def load_scoring_params():
    """Scoring 파라미터 로드"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_golden_set():
    """Golden Set 테스트 케이스 로드"""
    with open(GOLDEN_SET_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


# ============================================================
# Scoring 함수 (간소화된 구현)
# 실제 engine.py와 동기화 필요
# ============================================================

def calculate_eng_fit(inputs: dict, params: dict) -> dict:
    """Eng-Fit 계산 (CMC Risk)"""
    eng = params['eng_fit']
    
    # 기본값 처리
    logP = inputs.get('logP') or 0.0
    DAR = inputs.get('DAR') or 0.0
    h_patch = inputs.get('h_patch') or 0.0
    proc_complexity = inputs.get('proc_complexity') or 0.0
    anal_difficulty = inputs.get('anal_difficulty') or 0.0
    missing_features = inputs.get('missing_features') or []
    
    # 불확실성 페널티
    unc_penalty = len(missing_features) * 15.0 if missing_features else 0.0
    
    # AggRisk
    agg_risk = (
        eng['coefficients']['omega_logP'] * max(0, logP - eng['thresholds']['logP_optimal'])
        + eng['coefficients']['omega_DAR'] * max(0, DAR - eng['thresholds']['DAR_optimal'])
        + eng['coefficients']['omega_patch'] * h_patch * 100
    )
    agg_risk = min(100, max(0, agg_risk))
    
    # ProcRisk
    proc_risk = proc_complexity * 100
    
    # AnalRisk
    anal_risk = anal_difficulty * 100
    
    # CMC_Risk
    cmc_risk = (
        eng['weights']['w_agg'] * agg_risk
        + eng['weights']['w_proc'] * proc_risk
        + eng['weights']['w_anal'] * anal_risk
        + eng['weights']['w_unc'] * unc_penalty
    )
    cmc_risk = min(100, max(0, cmc_risk))
    
    eng_fit = 100 - cmc_risk
    
    return {
        'eng_fit': round(eng_fit, 2),
        'agg_risk': round(agg_risk, 2),
        'proc_risk': round(proc_risk, 2),
        'anal_risk': round(anal_risk, 2),
        'unc_penalty': round(unc_penalty, 2),
    }


def calculate_bio_fit(inputs: dict, params: dict) -> dict:
    """Bio-Fit 계산 (Biological Efficacy)"""
    bio = params['bio_fit']
    
    tumor_expr = inputs.get('tumor_expression') or 0.0
    normal_expr = inputs.get('normal_expression') or 0.0
    internalization = inputs.get('internalization') or 0.0
    heterogeneity = inputs.get('heterogeneity') or 0.0
    accessibility = inputs.get('accessibility') or 0.0
    bystander_need = inputs.get('bystander_need') or 0.0
    bystander_cap = inputs.get('bystander_capability') or 0.0
    
    import math
    
    # DEA
    dea = 50 + bio['coefficients']['k_dea'] * (
        math.log2(tumor_expr + 1) - math.log2(normal_expr + 1)
    )
    dea = min(100, max(0, dea))
    
    # INT
    int_score = 100 * internalization
    int_penalty = max(0, bio['coefficients']['int_threshold'] - int_score)
    
    # HET
    het_pen = 100 * heterogeneity
    
    # ACC
    acc_pen = 100 * (1 - accessibility)
    
    # BS (Bystander Match)
    bs_match = 100 * (1 - abs(bystander_need - bystander_cap))
    
    # BioRisk
    bio_risk = (
        bio['weights']['w_dea'] * (100 - dea)
        + bio['weights']['w_int'] * int_penalty
        + bio['weights']['w_het'] * het_pen
        + bio['weights']['w_acc'] * acc_pen
        + bio['weights']['w_bs'] * (100 - bs_match)
    )
    bio_risk = min(100, max(0, bio_risk))
    
    bio_fit = 100 - bio_risk
    
    return {
        'bio_fit': round(bio_fit, 2),
        'dea': round(dea, 2),
        'int': round(int_score, 2),
        'het_pen': round(het_pen, 2),
    }


def calculate_safety_fit(inputs: dict, params: dict) -> dict:
    """Safety-Fit 계산"""
    safety = params['safety_fit']
    
    import math
    
    normal_expr = inputs.get('normal_expression_max') or 0.0
    critical_flag = 1 if inputs.get('critical_tissue_flag') else 0
    payload_hazard = inputs.get('payload_hazard') or 0.0
    cleavage_risk = inputs.get('cleavage_risk') or 0.0
    systemic = inputs.get('systemic_exposure') or 0.0
    negative = inputs.get('negative_signal') or 0.0
    
    # OOT
    oot = (
        safety['coefficients']['k_oot'] * math.log2(normal_expr + 1)
        + safety['coefficients']['k_crit'] * critical_flag
    )
    oot = min(100, max(0, oot))
    
    # PH
    ph = 100 * payload_hazard
    
    # CLV
    clv = 100 * cleavage_risk
    
    # SAR
    sar = 100 * systemic
    
    # NEG
    neg = 100 * negative
    
    # SafetyRisk
    safety_risk = (
        safety['weights']['w_oot'] * oot
        + safety['weights']['w_haz'] * ph
        + safety['weights']['w_clv'] * clv
        + safety['weights']['w_sar'] * sar
        + safety['weights']['w_neg'] * neg
    )
    safety_risk = min(100, max(0, safety_risk))
    
    safety_fit = 100 - safety_risk
    
    return {
        'safety_fit': round(safety_fit, 2),
        'oot': round(oot, 2),
        'ph': round(ph, 2),
        'neg': round(neg, 2),
    }


def calculate_total_fit(inputs: dict, params: dict) -> dict:
    """Total-Fit 계산 (종합 점수)"""
    total = params['total_fit']
    
    eng = inputs.get('eng_fit') or 0.0
    bio = inputs.get('bio_fit') or 0.0
    safety = inputs.get('safety_fit') or 0.0
    evidence = inputs.get('evidence_fit') or 0.0
    
    total_fit = (
        total['weights']['eng'] * eng
        + total['weights']['bio'] * bio
        + total['weights']['safety'] * safety
        + total['weights']['evidence'] * evidence
    )
    
    return {
        'total_fit': round(total_fit, 2),
    }


# ============================================================
# 테스트 케이스
# ============================================================

class TestScoringRegression:
    """Golden Set 기반 스코어링 회귀 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """테스트 설정"""
        self.params = load_scoring_params()
        self.golden_set = load_golden_set()
        self.tolerance = self.golden_set.get('tolerance', 5.0)
    
    def get_cases_by_category(self, category: str):
        """카테고리별 테스트 케이스 반환"""
        return [
            c for c in self.golden_set.get('cases', [])
            if c.get('category') == category
        ]
    
    @pytest.mark.parametrize("case_id", [
        "eng_optimal", "eng_high_logp", "eng_high_dar", "eng_missing_data"
    ])
    def test_eng_fit_cases(self, case_id):
        """Eng-Fit 테스트 케이스"""
        cases = {c['id']: c for c in self.golden_set.get('cases', [])}
        case = cases.get(case_id)
        
        if not case:
            pytest.skip(f"Case {case_id} not found")
        
        result = calculate_eng_fit(case['inputs'], self.params)
        expected = case['expected']
        
        for key, expected_value in expected.items():
            if key in result:
                actual = result[key]
                diff = abs(actual - expected_value)
                assert diff <= self.tolerance, (
                    f"Case '{case_id}': {key} = {actual}, expected {expected_value} (±{self.tolerance})"
                )
    
    @pytest.mark.parametrize("case_id", [
        "bio_optimal", "bio_low_dea", "bio_poor_internalization", "bio_high_heterogeneity"
    ])
    def test_bio_fit_cases(self, case_id):
        """Bio-Fit 테스트 케이스"""
        cases = {c['id']: c for c in self.golden_set.get('cases', [])}
        case = cases.get(case_id)
        
        if not case:
            pytest.skip(f"Case {case_id} not found")
        
        result = calculate_bio_fit(case['inputs'], self.params)
        expected = case['expected']
        
        for key, expected_value in expected.items():
            if key in result:
                actual = result[key]
                diff = abs(actual - expected_value)
                assert diff <= self.tolerance, (
                    f"Case '{case_id}': {key} = {actual}, expected {expected_value} (±{self.tolerance})"
                )
    
    @pytest.mark.parametrize("case_id", [
        "safety_optimal", "safety_high_offtarget", "safety_toxic_payload", "safety_negative_signal"
    ])
    def test_safety_fit_cases(self, case_id):
        """Safety-Fit 테스트 케이스"""
        cases = {c['id']: c for c in self.golden_set.get('cases', [])}
        case = cases.get(case_id)
        
        if not case:
            pytest.skip(f"Case {case_id} not found")
        
        result = calculate_safety_fit(case['inputs'], self.params)
        expected = case['expected']
        
        for key, expected_value in expected.items():
            if key in result:
                actual = result[key]
                diff = abs(actual - expected_value)
                assert diff <= self.tolerance, (
                    f"Case '{case_id}': {key} = {actual}, expected {expected_value} (±{self.tolerance})"
                )
    
    @pytest.mark.parametrize("case_id", [
        "total_balanced", "total_bio_focused", "total_safety_concern"
    ])
    def test_total_fit_cases(self, case_id):
        """Total-Fit 테스트 케이스"""
        cases = {c['id']: c for c in self.golden_set.get('cases', [])}
        case = cases.get(case_id)
        
        if not case:
            pytest.skip(f"Case {case_id} not found")
        
        result = calculate_total_fit(case['inputs'], self.params)
        expected = case['expected']
        
        for key, expected_value in expected.items():
            if key in result:
                actual = result[key]
                diff = abs(actual - expected_value)
                assert diff <= self.tolerance, (
                    f"Case '{case_id}': {key} = {actual}, expected {expected_value} (±{self.tolerance})"
                )
    
    def test_scoring_params_version(self):
        """Scoring 파라미터 버전 확인"""
        assert self.params.get('version') == '0.2', \
            f"Expected scoring_params version 0.2, got {self.params.get('version')}"
    
    def test_weights_sum_to_one(self):
        """가중치 합계가 1.0인지 확인"""
        # Eng-Fit
        eng_weights = self.params['eng_fit']['weights']
        eng_sum = sum(eng_weights.values())
        assert abs(eng_sum - 1.0) < 0.01, f"Eng-Fit weights sum: {eng_sum}"
        
        # Bio-Fit
        bio_weights = self.params['bio_fit']['weights']
        bio_sum = sum(bio_weights.values())
        assert abs(bio_sum - 1.0) < 0.01, f"Bio-Fit weights sum: {bio_sum}"
        
        # Safety-Fit
        safety_weights = self.params['safety_fit']['weights']
        safety_sum = sum(safety_weights.values())
        assert abs(safety_sum - 1.0) < 0.01, f"Safety-Fit weights sum: {safety_sum}"
        
        # Total-Fit
        total_weights = self.params['total_fit']['weights']
        total_sum = sum(total_weights.values())
        assert abs(total_sum - 1.0) < 0.01, f"Total-Fit weights sum: {total_sum}"


# ============================================================
# 메인 실행
# ============================================================

if __name__ == "__main__":
    # 직접 실행 시 간단한 테스트
    params = load_scoring_params()
    golden = load_golden_set()
    
    print(f"Scoring Params Version: {params['version']}")
    print(f"Golden Set Version: {golden['version']}")
    print(f"Total Cases: {len(golden.get('cases', []))}")
    print(f"Tolerance: ±{golden.get('tolerance', 5.0)}%")
    
    # 첫 번째 케이스 테스트
    case = golden['cases'][0]
    print(f"\nTest Case: {case['id']} - {case['name']}")
    
    if case['category'] == 'eng_fit':
        result = calculate_eng_fit(case['inputs'], params)
        print(f"  Inputs: {case['inputs']}")
        print(f"  Result: {result}")
        print(f"  Expected: {case['expected']}")
