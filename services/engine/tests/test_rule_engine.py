"""
Rule Engine Tests
- 표현식 평가 테스트
- 룰 평가 테스트
- 결정론 테스트
- YAML 스키마 검증 테스트
"""
import pytest
from typing import Dict, Any

from app.rules import (
    SafeExpressionEvaluator,
    RuleEngine,
    RuleLoader,
    RuleSet,
    Rule,
    RuleResult,
    EvaluationResult,
    CandidateFeatures,
    ActionType,
    Severity,
)


# ============================================
# SafeExpressionEvaluator Tests
# ============================================

class TestSafeExpressionEvaluator:
    """표현식 평가기 테스트"""
    
    @pytest.fixture
    def evaluator(self):
        return SafeExpressionEvaluator()
    
    @pytest.fixture
    def context(self):
        return {
            "DAR": 6.0,
            "LogP": 4.5,
            "AggRisk": 35.0,
            "payload_class": "cytotoxic",
            "critical_tissue_expression": True,
            "clinical_failure_count": 2,
        }
    
    def test_greater_than(self, evaluator, context):
        """> 연산자"""
        result, reason = evaluator.evaluate("DAR > 4", context)
        assert result is True
        assert "DAR" in reason
        
        result, reason = evaluator.evaluate("DAR > 8", context)
        assert result is False
    
    def test_greater_equal(self, evaluator, context):
        """>= 연산자"""
        result, reason = evaluator.evaluate("DAR >= 6", context)
        assert result is True
        
        result, reason = evaluator.evaluate("DAR >= 6.0", context)
        assert result is True
    
    def test_less_than(self, evaluator, context):
        """< 연산자"""
        result, reason = evaluator.evaluate("AggRisk < 40", context)
        assert result is True
        
        result, reason = evaluator.evaluate("AggRisk < 30", context)
        assert result is False
    
    def test_equal(self, evaluator, context):
        """== 연산자"""
        result, reason = evaluator.evaluate("payload_class == 'cytotoxic'", context)
        assert result is True
        
        result, reason = evaluator.evaluate("payload_class == 'withdrawn'", context)
        assert result is False
    
    def test_not_equal(self, evaluator, context):
        """!= 연산자"""
        result, reason = evaluator.evaluate("payload_class != 'withdrawn'", context)
        assert result is True
    
    def test_boolean(self, evaluator, context):
        """불리언 평가"""
        result, reason = evaluator.evaluate("critical_tissue_expression == true", context)
        assert result is True
        
        result, reason = evaluator.evaluate("critical_tissue_expression == false", context)
        assert result is False
    
    def test_integer_comparison(self, evaluator, context):
        """정수 비교"""
        result, reason = evaluator.evaluate("clinical_failure_count > 0", context)
        assert result is True
        
        result, reason = evaluator.evaluate("clinical_failure_count == 2", context)
        assert result is True
    
    def test_missing_field(self, evaluator, context):
        """존재하지 않는 필드"""
        result, reason = evaluator.evaluate("unknown_field > 0", context)
        assert result is False
        assert "not found" in reason
    
    def test_contains_list(self, evaluator):
        """contains - 리스트"""
        context = {"tissues": ["liver", "kidney", "heart"]}
        result, reason = evaluator.evaluate("tissues contains 'liver'", context)
        assert result is True
    
    def test_contains_string(self, evaluator):
        """contains - 문자열"""
        context = {"name": "anti-HER2-MMAE-ADC"}
        result, reason = evaluator.evaluate("name contains 'MMAE'", context)
        assert result is True
    
    def test_in_operator(self, evaluator, context):
        """in 연산자"""
        result, reason = evaluator.evaluate(
            "payload_class in ['cytotoxic', 'immunomodulator']", 
            context
        )
        assert result is True
    
    def test_is_null(self, evaluator):
        """is_null 연산자"""
        context = {"value": None, "other": 123}
        result, reason = evaluator.evaluate("value is_null", context)
        assert result is True
        
        result, reason = evaluator.evaluate("other is_null", context)
        assert result is False
    
    def test_complex_condition_all(self, evaluator, context):
        """복합 조건 - all (AND)"""
        condition = {
            "all": [
                {"field": "DAR", "operator": ">", "value": 4},
                {"field": "LogP", "operator": ">", "value": 4},
            ]
        }
        result, reason = evaluator.evaluate_condition(condition, context)
        assert result is True
        assert "AND" in reason
    
    def test_complex_condition_any(self, evaluator, context):
        """복합 조건 - any (OR)"""
        condition = {
            "any": [
                {"field": "DAR", "operator": ">", "value": 10},  # False
                {"field": "LogP", "operator": ">", "value": 4},  # True
            ]
        }
        result, reason = evaluator.evaluate_condition(condition, context)
        assert result is True
    
    def test_invalid_expression(self, evaluator, context):
        """잘못된 표현식"""
        result, reason = evaluator.evaluate("this is not valid", context)
        assert result is False
        assert "invalid" in reason.lower()


# ============================================
# RuleEngine Tests
# ============================================

class TestRuleEngine:
    """Rule Engine 테스트"""
    
    @pytest.fixture
    def sample_ruleset_dict(self) -> Dict[str, Any]:
        return {
            "version": "test_0.1",
            "penalty_policy": "sum",
            "rules": [
                {
                    "id": "hr_test",
                    "name": "Test Hard Reject",
                    "priority": 1,
                    "condition": {"expression": "DAR > 8"},
                    "action": {"type": "hard_reject", "message": "DAR too high"}
                },
                {
                    "id": "pn_test",
                    "name": "Test Penalty",
                    "priority": 10,
                    "condition": {"expression": "LogP > 4.0"},
                    "action": {"type": "penalty", "value": 10, "message": "High LogP"}
                },
                {
                    "id": "al_test",
                    "name": "Test Alert",
                    "priority": 20,
                    "condition": {"expression": "critical_tissue_expression == true"},
                    "action": {"type": "alert", "severity": "warning", "message": "Critical tissue"}
                },
                {
                    "id": "pr_test",
                    "name": "Test Protocol",
                    "priority": 30,
                    "condition": {"expression": "AggRisk > 30"},
                    "action": {"type": "require_protocol", "template_id": "sec_v1", "message": "SEC required"}
                },
            ]
        }
    
    @pytest.fixture
    def engine(self, sample_ruleset_dict) -> RuleEngine:
        ruleset = RuleSet.from_dict(sample_ruleset_dict)
        return RuleEngine(ruleset=ruleset)
    
    def test_no_hard_reject(self, engine):
        """하드리젝트 없는 경우"""
        features = CandidateFeatures(DAR=4.0, LogP=3.0, AggRisk=20.0)
        result = engine.evaluate_candidate(features)
        
        assert result.hard_rejected is False
        assert result.total_penalty == 0
    
    def test_hard_reject(self, engine):
        """하드리젝트 발생"""
        features = CandidateFeatures(DAR=9.0)
        result = engine.evaluate_candidate(features)
        
        assert result.hard_rejected is True
        assert "DAR" in result.reject_reason
    
    def test_penalty_accumulation(self, engine):
        """페널티 누적 (sum 정책)"""
        features = CandidateFeatures(LogP=4.5)
        result = engine.evaluate_candidate(features)
        
        assert result.total_penalty == 10
        assert "pn_test" in result.penalty_breakdown
    
    def test_alert_collection(self, engine):
        """Alert 수집"""
        features = CandidateFeatures(critical_tissue_expression=True)
        result = engine.evaluate_candidate(features)
        
        assert len(result.alerts) == 1
        assert result.alerts[0].rule_id == "al_test"
    
    def test_protocol_requirement(self, engine):
        """프로토콜 요구사항"""
        features = CandidateFeatures(AggRisk=40.0)
        result = engine.evaluate_candidate(features)
        
        assert "sec_v1" in result.required_protocols
    
    def test_multiple_hits(self, engine):
        """여러 룰 동시 적중"""
        features = CandidateFeatures(
            DAR=4.0,
            LogP=4.5,
            AggRisk=40.0,
            critical_tissue_expression=True
        )
        result = engine.evaluate_candidate(features)
        
        assert result.hard_rejected is False
        assert result.total_penalty == 10  # pn_test
        assert len(result.alerts) == 1  # al_test
        assert "sec_v1" in result.required_protocols  # pr_test
        assert len(result.hits) == 3


# ============================================
# Determinism Tests
# ============================================

class TestDeterminism:
    """결정론 테스트 - 동일 입력에서 항상 동일 출력"""
    
    def test_rule_evaluation_determinism(self):
        """룰 평가 결정론"""
        ruleset_dict = {
            "version": "det_test",
            "penalty_policy": "sum",
            "rules": [
                {"id": "a_rule", "priority": 10, "condition": {"expression": "DAR > 4"}, 
                 "action": {"type": "penalty", "value": 5}},
                {"id": "b_rule", "priority": 10, "condition": {"expression": "LogP > 4"}, 
                 "action": {"type": "penalty", "value": 10}},
                {"id": "c_rule", "priority": 5, "condition": {"expression": "AggRisk > 30"}, 
                 "action": {"type": "alert", "message": "High AggRisk"}},
            ]
        }
        
        ruleset = RuleSet.from_dict(ruleset_dict)
        engine = RuleEngine(ruleset=ruleset)
        features = CandidateFeatures(DAR=5.0, LogP=4.5, AggRisk=35.0)
        
        # 100번 평가
        results = [engine.evaluate_candidate(features) for _ in range(100)]
        
        # 모든 결과가 동일해야 함
        first = results[0]
        for r in results[1:]:
            assert r.total_penalty == first.total_penalty
            assert r.required_protocols == first.required_protocols
            assert len(r.hits) == len(first.hits)
            assert [h.rule_id for h in r.hits] == [h.rule_id for h in first.hits]
    
    def test_rule_order_by_priority_and_id(self):
        """룰 정렬 순서 확인 (priority ASC, id ASC)"""
        ruleset_dict = {
            "version": "order_test",
            "rules": [
                {"id": "z_rule", "priority": 10, "condition": {"expression": "DAR > 0"}, 
                 "action": {"type": "alert"}},
                {"id": "a_rule", "priority": 10, "condition": {"expression": "DAR > 0"}, 
                 "action": {"type": "alert"}},
                {"id": "m_rule", "priority": 5, "condition": {"expression": "DAR > 0"}, 
                 "action": {"type": "alert"}},
            ]
        }
        
        ruleset = RuleSet.from_dict(ruleset_dict)
        sorted_rules = ruleset.get_sorted_rules()
        
        # priority 5가 먼저, 그 다음 priority 10에서 a가 z보다 먼저
        assert sorted_rules[0].id == "m_rule"  # priority 5
        assert sorted_rules[1].id == "a_rule"  # priority 10, id=a
        assert sorted_rules[2].id == "z_rule"  # priority 10, id=z


# ============================================
# YAML Schema Validation Tests
# ============================================

class TestYAMLSchemaValidation:
    """YAML 스키마 검증 테스트"""
    
    @pytest.fixture
    def loader(self):
        return RuleLoader()
    
    def test_valid_ruleset(self, loader):
        """유효한 룰셋"""
        data = {
            "version": "0.1",
            "rules": [
                {
                    "id": "test_rule",
                    "condition": {"expression": "DAR > 4"},
                    "action": {"type": "alert"}
                }
            ]
        }
        # Should not raise
        loader.validate_schema(data)
    
    def test_missing_version(self, loader):
        """version 필드 누락"""
        data = {"rules": []}
        
        with pytest.raises(Exception) as exc:
            loader.validate_schema(data)
        assert "version" in str(exc.value).lower()
    
    def test_missing_rules(self, loader):
        """rules 필드 누락"""
        data = {"version": "0.1"}
        
        with pytest.raises(Exception) as exc:
            loader.validate_schema(data)
        assert "rules" in str(exc.value).lower()
    
    def test_rule_missing_id(self, loader):
        """룰 id 누락"""
        data = {
            "version": "0.1",
            "rules": [
                {"condition": {"expression": "DAR > 4"}, "action": {"type": "alert"}}
            ]
        }
        
        with pytest.raises(Exception) as exc:
            loader.validate_schema(data)
        assert "id" in str(exc.value).lower()
    
    def test_rule_missing_condition(self, loader):
        """룰 condition 누락"""
        data = {
            "version": "0.1",
            "rules": [
                {"id": "test", "action": {"type": "alert"}}
            ]
        }
        
        with pytest.raises(Exception) as exc:
            loader.validate_schema(data)
        assert "condition" in str(exc.value).lower()
    
    def test_penalty_requires_value(self, loader):
        """penalty 액션은 value 필수"""
        data = {
            "version": "0.1",
            "rules": [
                {
                    "id": "test",
                    "condition": {"expression": "DAR > 4"},
                    "action": {"type": "penalty"}  # value 없음
                }
            ]
        }
        
        with pytest.raises(Exception) as exc:
            loader.validate_schema(data)
        assert "value" in str(exc.value).lower()
    
    def test_require_protocol_requires_template_id(self, loader):
        """require_protocol 액션은 template_id 필수"""
        data = {
            "version": "0.1",
            "rules": [
                {
                    "id": "test",
                    "condition": {"expression": "DAR > 4"},
                    "action": {"type": "require_protocol"}  # template_id 없음
                }
            ]
        }
        
        with pytest.raises(Exception) as exc:
            loader.validate_schema(data)
        assert "template_id" in str(exc.value).lower()
