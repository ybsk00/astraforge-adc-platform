"""
Golden Set Validator Service
실험 데이터 기반 산식 정합성 검증 및 회귀 테스트

기능:
- 단위 정규화 (nM, pM, %, hr 등)
- Assay 우선순위 및 품질 플래그 반영
- 다차원 지표 산출 (MAE, RMSE, Spearman, Top-K Overlap)
- 검증 결과 DB 적재 (golden_validation_runs, golden_validation_metrics)
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import structlog
import numpy as np
from scipy.stats import spearmanr, kendalltau

logger = structlog.get_logger()

@dataclass
class ValidationMetric:
    axis: str
    metric: str
    value: float
    threshold: float
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)

class GoldenSetValidator:
    """Golden Set 검증 엔진"""
    
    def __init__(self, db_client):
        self.db = db_client
        self.logger = logger.bind(service="golden_set_validator")
        
        # 단위 변환 계수 (기준: nM, %, hr)
        self.unit_converters = {
            "nM": 1.0,
            "pM": 0.001,
            "uM": 1000.0,
            "mM": 1000000.0
        }
        
        # Assay 우선순위 (높을수록 신뢰도 높음)
        self.assay_priority = {
            "in_vivo": 100,
            "cell_line": 80,
            "spr": 60,
            "sec": 50,
            "dls": 40,
            "estimated": 20
        }

    async def run_validation(self, scoring_version: str, dataset_version: str = "v1.0") -> Dict[str, Any]:
        """전체 Golden Set 검증 실행"""
        self.logger.info("golden_validation_started", scoring_version=scoring_version, dataset_version=dataset_version)
        
        try:
            # 1. 데이터 로드
            candidates = await self._load_golden_candidates()
            measurements = await self._load_golden_measurements()
            
            # 2. 정규화 및 정답셋(y_true) 구축
            y_true_map = self._normalize_and_aggregate(measurements)
            
            # 3. 시스템 점수(y_pred) 로드
            y_pred_map = await self._fetch_system_scores(scoring_version, list(y_true_map.keys()))
            
            # 4. 지표 산출
            all_metrics = []
            axes = ["Bio", "Safety", "Eng", "Clin"]
            
            for axis in axes:
                axis_metrics = self._calculate_axis_metrics(axis, y_true_map, y_pred_map)
                all_metrics.extend(axis_metrics)
                
            # 5. 랭킹 안정성 (Overall)
            overall_metrics = self._calculate_ranking_metrics(y_true_map, y_pred_map)
            all_metrics.extend(overall_metrics)
            
            # 6. 결과 저장 및 반환
            is_pass = all(m.passed for m in all_metrics)
            run_id = await self._save_results(scoring_version, dataset_version, is_pass, all_metrics)
            
            return {
                "run_id": run_id,
                "pass": is_pass,
                "metrics": [vars(m) for m in all_metrics]
            }

        except Exception as e:
            self.logger.error("golden_validation_failed", error=str(e))
            raise

    async def _load_golden_candidates(self) -> List[Dict[str, Any]]:
        res = await self.db.table("golden_candidates").select("*").execute()
        return res.data

    async def _load_golden_measurements(self) -> List[Dict[str, Any]]:
        res = await self.db.table("golden_measurements").select("*").execute()
        return res.data

    def _normalize_and_aggregate(self, measurements: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """측정치 정규화 및 후보별/축별 집계"""
        # candidate_id -> axis -> [values]
        raw_map = {}
        
        # Metric mapping to Axis
        metric_to_axis = {
            "IC50": "Bio",
            "Cytotoxicity": "Bio",
            "Aggregation_pct": "Eng",
            "SerumStability_hr": "Eng",
            "Toxicity_LD50": "Safety",
            "OffTarget_Binding": "Safety",
            "Clinical_Phase": "Clin"
        }

        for m in measurements:
            cid = m["candidate_id"]
            axis = metric_to_axis.get(m["metric_name"])
            if not axis: continue
            
            # 단위 변환
            val = float(m["value"])
            unit = m.get("unit")
            if unit in self.unit_converters:
                val *= self.unit_converters[unit]
                
            # 품질 가중치 (Assay 우선순위)
            priority = self.assay_priority.get(m.get("assay_type", "").lower(), 50)
            
            if cid not in raw_map: raw_map[cid] = {}
            if axis not in raw_map[cid]: raw_map[cid][axis] = []
            raw_map[cid][axis].append((val, priority))

        # 집계 (가중 평균 또는 중앙값)
        agg_map = {}
        for cid, axes in raw_map.items():
            agg_map[cid] = {}
            for axis, vals in axes.items():
                # 가중 평균
                total_val = sum(v * p for v, p in vals)
                total_p = sum(p for v, p in vals)
                agg_map[cid][axis] = total_val / total_p if total_p > 0 else 0.0
                
        return agg_map

    async def _fetch_system_scores(self, scoring_version: str, candidate_ids: List[str]) -> Dict[str, Dict[str, float]]:
        """시스템이 계산한 점수 조회 (디자인 런 결과 등에서 추출)"""
        # MVP: 실제 운영 환경에서는 특정 런의 결과를 가져오거나 즉시 계산
        # 여기서는 candidate_id -> axis -> score 맵을 반환한다고 가정
        res = await self.db.table("design_candidates")\
            .select("id, bio_fit, safety_fit, eng_fit, clin_fit")\
            .in_("id", candidate_ids)\
            .execute()
            
        score_map = {}
        for r in res.data:
            score_map[r["id"]] = {
                "Bio": r["bio_fit"],
                "Safety": r["safety_fit"],
                "Eng": r["eng_fit"],
                "Clin": r["clin_fit"]
            }
        return score_map

    def _calculate_axis_metrics(self, axis: str, y_true_map: Dict, y_pred_map: Dict) -> List[ValidationMetric]:
        """축별 오차 및 상관계수 산출"""
        y_true, y_pred = [], []
        for cid in y_true_map:
            if cid in y_pred_map and axis in y_true_map[cid]:
                y_true.append(y_true_map[cid][axis])
                y_pred.append(y_pred_map[cid][axis])
        
        if not y_true: return []
        
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred)**2))
        
        # Spearman Rank Correlation
        corr, _ = spearmanr(y_true, y_pred)
        
        metrics = [
            ValidationMetric(axis, "MAE", mae, 15.0, mae <= 15.0),
            ValidationMetric(axis, "Spearman", corr, 0.7, corr >= 0.7 if not np.isnan(corr) else False)
        ]
        return metrics

    def _calculate_ranking_metrics(self, y_true_map: Dict, y_pred_map: Dict) -> List[ValidationMetric]:
        """전체 랭킹 안정성 및 Top-K Overlap 산출"""
        # 총점 기반 랭킹 비교
        true_totals = {cid: sum(axes.values()) for cid, axes in y_true_map.items()}
        pred_totals = {cid: sum(axes.values()) for cid, axes in y_pred_map.items() if cid in y_true_map}
        
        if len(true_totals) < 2: return []
        
        sorted_true = sorted(true_totals.keys(), key=lambda k: true_totals[k], reverse=True)
        sorted_pred = sorted(pred_totals.keys(), key=lambda k: pred_totals[k], reverse=True)
        
        # Top-K Overlap (K=5 or len/2)
        k = min(5, len(sorted_true))
        top_true = set(sorted_true[:k])
        top_pred = set(sorted_pred[:k])
        overlap = len(top_true.intersection(top_pred)) / k
        
        # Kendall Tau
        tau, _ = kendalltau(
            [true_totals[cid] for cid in sorted_true],
            [pred_totals[cid] for cid in sorted_true]
        )
        
        return [
            ValidationMetric("overall", "TopKOverlap", overlap, 0.6, overlap >= 0.6),
            ValidationMetric("overall", "KendallTau", tau, 0.5, tau >= 0.5 if not np.isnan(tau) else False)
        ]

    async def _save_results(self, scoring_version: str, dataset_version: str, is_pass: bool, metrics: List[ValidationMetric]) -> str:
        """검증 결과를 DB에 저장"""
        # 1. Run 저장
        run_res = await self.db.table("golden_validation_runs").insert({
            "scoring_version": scoring_version,
            "dataset_version": dataset_version,
            "pass": is_pass,
            "summary": {m.metric: m.value for m in metrics if m.axis == "overall"}
        }).execute()
        
        run_id = run_res.data[0]["id"]
        
        # 2. Metrics 저장
        metric_data = []
        for m in metrics:
            metric_data.append({
                "run_id": run_id,
                "axis": m.axis,
                "metric": m.metric,
                "value": m.value,
                "threshold": m.threshold,
                "pass": m.passed,
                "details": m.details
            })
            
        await self.db.table("golden_validation_metrics").insert(metric_data).execute()
        return run_id

def get_golden_validator(db_client) -> GoldenSetValidator:
    return GoldenSetValidator(db_client)
