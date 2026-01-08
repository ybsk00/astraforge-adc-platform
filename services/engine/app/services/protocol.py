"""
Protocol Generator Service
실험 프로토콜 템플릿 기반 생성

체크리스트 §5.9 기반:
- SEC (Aggregation check)
- HIC (Hydrophobicity profile)
- Plasma stability + free drug LC-MS
- Internalization kinetics
- Cytotoxicity panel
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class ProtocolStep:
    """프로토콜 단계"""
    step_number: int
    title: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_output: str = ""
    duration_hours: Optional[float] = None


@dataclass
class Protocol:
    """생성된 프로토콜"""
    template_id: str
    name: str
    version: str
    candidate_id: str
    steps: List[ProtocolStep] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    triggered_by: Optional[str] = None  # rule_id that triggered this
    status: str = "draft"
    
    @property
    def total_duration_hours(self) -> float:
        return sum(s.duration_hours or 0 for s in self.steps)


# ============================================================
# 프로토콜 템플릿 정의
# ============================================================

PROTOCOL_TEMPLATES = {
    "sec": {
        "id": "sec",
        "name": "Size Exclusion Chromatography (SEC)",
        "description": "응집도 및 크기 분포 분석",
        "version": "1.0",
        "trigger_rules": ["AggRisk"],  # 이 위험이 높으면 자동 추가
        "trigger_threshold": 30.0,
        "steps": [
            {
                "step_number": 1,
                "title": "샘플 준비",
                "description": "ADC 샘플 1mg/mL로 희석, 원심분리 (14,000g, 10분)",
                "duration_hours": 0.5
            },
            {
                "step_number": 2,
                "title": "SEC 분석",
                "description": "TSKgel G3000SWXL 컬럼, PBS 이동상, 0.5mL/min",
                "parameters": {"column": "TSKgel G3000SWXL", "flow_rate": 0.5},
                "duration_hours": 1.0
            },
            {
                "step_number": 3,
                "title": "데이터 분석",
                "description": "모노머 피크 면적 비율 계산, 응집체/분해물 정량",
                "expected_output": "모노머 순도 >95%",
                "duration_hours": 0.5
            }
        ]
    },
    
    "hic": {
        "id": "hic",
        "name": "Hydrophobic Interaction Chromatography (HIC)",
        "description": "소수성 프로파일 및 DAR 분포 분석",
        "version": "1.0",
        "trigger_rules": ["AggRisk", "CMC_Risk"],
        "trigger_threshold": 25.0,
        "steps": [
            {
                "step_number": 1,
                "title": "샘플 준비",
                "description": "ADC 샘플 2M 암모늄 설페이트 용액에 희석",
                "duration_hours": 0.3
            },
            {
                "step_number": 2,
                "title": "HIC 분석",
                "description": "Butyl-NPR 컬럼, 암모늄 설페이트 그래디언트",
                "parameters": {"column": "Butyl-NPR", "gradient": "2M to 0M (NH4)2SO4"},
                "duration_hours": 1.5
            },
            {
                "step_number": 3,
                "title": "DAR 계산",
                "description": "피크 면적으로 DAR 분포 계산 (DAR 0-8)",
                "expected_output": "평균 DAR 및 분포 리포트",
                "duration_hours": 0.5
            }
        ]
    },
    
    "plasma_stability": {
        "id": "plasma_stability",
        "name": "Plasma Stability Assay",
        "description": "혈장 안정성 및 유리 약물 방출 분석",
        "version": "1.0",
        "trigger_rules": ["CLV", "SafetyRisk"],
        "trigger_threshold": 30.0,
        "steps": [
            {
                "step_number": 1,
                "title": "혈장 인큐베이션",
                "description": "인간/마우스 혈장에 ADC 인큐베이션 (37°C, 0/24/48/72h)",
                "parameters": {"temperature": 37, "timepoints": [0, 24, 48, 72]},
                "duration_hours": 72.0
            },
            {
                "step_number": 2,
                "title": "LC-MS/MS 분석",
                "description": "유리 페이로드 정량 (LC-MS/MS)",
                "duration_hours": 4.0
            },
            {
                "step_number": 3,
                "title": "안정성 계산",
                "description": "T1/2 계산 및 방출 속도 분석",
                "expected_output": "혈장 T1/2 >72h 권장",
                "duration_hours": 1.0
            }
        ]
    },
    
    "internalization": {
        "id": "internalization",
        "name": "Internalization Kinetics Assay",
        "description": "수용체 매개 세포 내재화 분석",
        "version": "1.0",
        "trigger_rules": ["DEA", "INT"],
        "trigger_threshold": 50.0,
        "steps": [
            {
                "step_number": 1,
                "title": "세포 준비",
                "description": "타겟 양성 세포주 배양 (confluence 80%)",
                "duration_hours": 48.0
            },
            {
                "step_number": 2,
                "title": "내재화 분석",
                "description": "형광 표지 ADC 처리, 시간별 공초점 현미경 이미징",
                "parameters": {"timepoints": [0, 15, 30, 60, 120, 240]},
                "duration_hours": 8.0
            },
            {
                "step_number": 3,
                "title": "정량 분석",
                "description": "내재화 속도 상수 계산",
                "expected_output": "t1/2 internalization < 30min 권장",
                "duration_hours": 2.0
            }
        ]
    },
    
    "cytotoxicity": {
        "id": "cytotoxicity",
        "name": "Cytotoxicity Panel",
        "description": "타겟 양성/음성 세포주 세포독성 분석",
        "version": "1.0",
        "trigger_rules": ["OOT", "SafetyRisk", "BioRisk"],
        "trigger_threshold": 25.0,
        "steps": [
            {
                "step_number": 1,
                "title": "세포주 준비",
                "description": "타겟 High/Low/Negative 세포주 각 2종 이상 준비",
                "parameters": {"cell_lines": ["Target-High", "Target-Low", "Target-Negative"]},
                "duration_hours": 72.0
            },
            {
                "step_number": 2,
                "title": "ADC 처리",
                "description": "농도 범위 처리 (0.001-100 nM), 72h 인큐베이션",
                "parameters": {"concentration_range": [0.001, 0.01, 0.1, 1, 10, 100]},
                "duration_hours": 72.0
            },
            {
                "step_number": 3,
                "title": "세포 생존율 측정",
                "description": "CellTiter-Glo 또는 MTT assay",
                "duration_hours": 4.0
            },
            {
                "step_number": 4,
                "title": "IC50 계산",
                "description": "각 세포주별 IC50 및 선택성 윈도우 계산",
                "expected_output": "Target-High IC50 < 1nM, 선택성 >100x",
                "duration_hours": 2.0
            }
        ]
    }
}


class ProtocolGeneratorService:
    """
    프로토콜 생성 서비스
    
    스코어 컴포넌트 기반으로 필요한 프로토콜 자동 선택/생성
    """
    
    def __init__(self, templates: Dict[str, Any] = None):
        self.templates = templates or PROTOCOL_TEMPLATES
        self.logger = logger.bind(service="protocol_generator")
    
    def generate_protocols(
        self,
        candidate_id: str,
        score_components: Dict[str, Any],
        force_templates: List[str] = None
    ) -> List[Protocol]:
        """
        후보에 대한 프로토콜 생성
        
        Args:
            candidate_id: 후보 ID
            score_components: 스코어 컴포넌트 (terms 포함)
            force_templates: 강제 추가할 템플릿 ID 목록
        
        Returns:
            List of Protocol objects
        """
        protocols = []
        triggered_templates = set()
        
        # 1. 스코어 기반 자동 선택
        for template_id, template in self.templates.items():
            trigger_rules = template.get("trigger_rules", [])
            threshold = template.get("trigger_threshold", 50.0)
            
            # 트리거 규칙 체크
            for rule in trigger_rules:
                if self._check_trigger(rule, score_components, threshold):
                    triggered_templates.add(template_id)
                    break
        
        # 2. 강제 템플릿 추가
        if force_templates:
            triggered_templates.update(force_templates)
        
        # 3. 프로토콜 생성
        for template_id in triggered_templates:
            template = self.templates.get(template_id)
            if template:
                protocol = self._create_protocol(candidate_id, template)
                protocols.append(protocol)
        
        self.logger.info(
            "protocols_generated",
            candidate_id=candidate_id,
            count=len(protocols),
            templates=list(triggered_templates)
        )
        
        return protocols
    
    def _check_trigger(
        self,
        rule: str,
        score_components: Dict[str, Any],
        threshold: float
    ) -> bool:
        """트리거 규칙 체크"""
        # 각 fit 타입의 terms 확인
        for fit_type in ["eng_fit", "bio_fit", "safety_fit"]:
            terms = score_components.get(fit_type, {}).get("terms", {})
            if rule in terms and terms[rule] >= threshold:
                return True
        
        return False
    
    def _create_protocol(
        self,
        candidate_id: str,
        template: Dict[str, Any]
    ) -> Protocol:
        """템플릿에서 프로토콜 생성"""
        steps = []
        
        for step_data in template.get("steps", []):
            steps.append(ProtocolStep(
                step_number=step_data.get("step_number", 0),
                title=step_data.get("title", ""),
                description=step_data.get("description", ""),
                parameters=step_data.get("parameters", {}),
                expected_output=step_data.get("expected_output", ""),
                duration_hours=step_data.get("duration_hours")
            ))
        
        return Protocol(
            template_id=template["id"],
            name=template["name"],
            version=template["version"],
            candidate_id=candidate_id,
            steps=steps,
            triggered_by=",".join(template.get("trigger_rules", [])),
            status="draft"
        )
    
    def to_db_format(self, protocol: Protocol) -> Dict[str, Any]:
        """DB 저장 형식 변환"""
        return {
            "candidate_id": protocol.candidate_id,
            "template_id": protocol.template_id,
            "protocol_type": protocol.template_id,
            "name": protocol.name,
            "version": protocol.version,
            "steps": [
                {
                    "step_number": s.step_number,
                    "title": s.title,
                    "description": s.description,
                    "parameters": s.parameters,
                    "expected_output": s.expected_output,
                    "duration_hours": s.duration_hours
                }
                for s in protocol.steps
            ],
            "total_duration_hours": protocol.total_duration_hours,
            "triggered_by": protocol.triggered_by,
            "status": protocol.status,
            "created_at": datetime.utcnow().isoformat()
        }
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """사용 가능한 템플릿 목록"""
        return [
            {
                "id": t["id"],
                "name": t["name"],
                "description": t["description"],
                "trigger_rules": t.get("trigger_rules", []),
                "trigger_threshold": t.get("trigger_threshold", 50.0)
            }
            for t in self.templates.values()
        ]


# 편의 함수
def get_protocol_service(templates: Dict[str, Any] = None) -> ProtocolGeneratorService:
    return ProtocolGeneratorService(templates)
