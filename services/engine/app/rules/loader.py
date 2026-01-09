"""
Rule Loader
YAML 룰셋 파일 로드 및 검증

구현 계획 v2 기반:
- 파일 시스템/DB에서 룰셋 로드
- 스키마 검증
- 버전 관리
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import structlog

from .models import RuleSet, Rule

logger = structlog.get_logger()


class RuleLoadError(Exception):
    """룰 로드 오류"""
    pass


class RuleSchemaError(Exception):
    """룰 스키마 오류"""
    pass


# 필수 필드 정의
REQUIRED_RULESET_FIELDS = ["version", "rules"]
REQUIRED_RULE_FIELDS = ["id", "condition", "action"]


class RuleLoader:
    """
    룰셋 로더
    
    - YAML 파일 로드
    - 스키마 검증
    - DB에서 로드 (선택)
    """
    
    def __init__(self, rulesets_dir: str = None):
        """
        Args:
            rulesets_dir: 룰셋 YAML 파일이 위치한 디렉토리
        """
        self.rulesets_dir = rulesets_dir or self._get_default_dir()
        self.logger = logger.bind(component="RuleLoader")
    
    def _get_default_dir(self) -> str:
        """기본 룰셋 디렉토리"""
        # 프로젝트 루트/config/rulesets
        base = Path(__file__).parent.parent.parent.parent.parent  # services/engine/../..
        return str(base / "config" / "rulesets")
    
    def load_from_file(self, filepath: str) -> RuleSet:
        """
        YAML 파일에서 룰셋 로드
        
        Args:
            filepath: 룰셋 YAML 파일 경로
            
        Returns:
            RuleSet
        """
        if not os.path.exists(filepath):
            raise RuleLoadError(f"Ruleset file not found: {filepath}")
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RuleLoadError(f"Invalid YAML format: {e}")
        
        # 스키마 검증
        self.validate_schema(data)
        
        # RuleSet 객체 생성
        ruleset = RuleSet.from_dict(data)
        
        self.logger.info(
            "ruleset_loaded",
            filepath=filepath,
            version=ruleset.version,
            rule_count=len(ruleset.rules)
        )
        
        return ruleset
    
    def load_by_version(self, version: str) -> RuleSet:
        """
        버전으로 룰셋 로드
        
        Args:
            version: 룰셋 버전 (예: "0.1")
            
        Returns:
            RuleSet
        """
        filename = f"ruleset_v{version}.yaml"
        filepath = os.path.join(self.rulesets_dir, filename)
        return self.load_from_file(filepath)
    
    def load_active(self) -> Optional[RuleSet]:
        """
        활성 룰셋 로드 (DB에서)
        
        Returns:
            RuleSet or None
        """
        # TODO: DB에서 is_active=True인 룰셋 로드
        # 현재는 파일 시스템에서 가장 높은 버전 로드
        try:
            versions = self.list_versions()
            if not versions:
                return None
            
            latest = sorted(versions, reverse=True)[0]
            return self.load_by_version(latest)
            
        except Exception as e:
            self.logger.warning("active_ruleset_load_failed", error=str(e))
            return None
    
    def list_versions(self) -> List[str]:
        """사용 가능한 룰셋 버전 목록"""
        if not os.path.exists(self.rulesets_dir):
            return []
        
        versions = []
        for filename in os.listdir(self.rulesets_dir):
            if filename.startswith("ruleset_v") and filename.endswith(".yaml"):
                # ruleset_v0.1.yaml -> 0.1
                version = filename[9:-5]  # Remove "ruleset_v" and ".yaml"
                versions.append(version)
        
        return versions
    
    def validate_schema(self, data: Dict[str, Any]):
        """
        룰셋 스키마 검증
        
        Raises:
            RuleSchemaError: 스키마 오류 시
        """
        # 필수 필드 체크
        for field in REQUIRED_RULESET_FIELDS:
            if field not in data:
                raise RuleSchemaError(f"Missing required field: {field}")
        
        # rules 배열 체크
        if not isinstance(data["rules"], list):
            raise RuleSchemaError("'rules' must be a list")
        
        # 개별 룰 검증
        for i, rule in enumerate(data["rules"]):
            self._validate_rule(rule, i)
    
    def _validate_rule(self, rule: Dict[str, Any], index: int):
        """개별 룰 검증"""
        for field in REQUIRED_RULE_FIELDS:
            if field not in rule:
                raise RuleSchemaError(f"Rule[{index}]: Missing required field '{field}'")
        
        # condition 검증
        condition = rule["condition"]
        if not isinstance(condition, dict) and not isinstance(condition, str):
            raise RuleSchemaError(f"Rule[{index}]: 'condition' must be dict or string")
        
        if isinstance(condition, dict):
            if not any(k in condition for k in ["expression", "all", "any"]):
                raise RuleSchemaError(
                    f"Rule[{index}]: condition must have 'expression', 'all', or 'any'"
                )
        
        # action 검증
        action = rule["action"]
        if "type" not in action:
            raise RuleSchemaError(f"Rule[{index}]: action missing 'type'")
        
        valid_types = ["hard_reject", "soft_reject", "penalty", "alert", "require_protocol"]
        if action["type"] not in valid_types:
            raise RuleSchemaError(
                f"Rule[{index}]: invalid action type '{action['type']}'. "
                f"Must be one of: {valid_types}"
            )
        
        # penalty 시 value 필수
        if action["type"] == "penalty" and "value" not in action:
            raise RuleSchemaError(f"Rule[{index}]: penalty action requires 'value'")
        
        # require_protocol 시 template_id 필수
        if action["type"] == "require_protocol" and "template_id" not in action:
            raise RuleSchemaError(
                f"Rule[{index}]: require_protocol action requires 'template_id'"
            )


def get_loader(rulesets_dir: str = None) -> RuleLoader:
    """RuleLoader 인스턴스 반환"""
    return RuleLoader(rulesets_dir=rulesets_dir)
