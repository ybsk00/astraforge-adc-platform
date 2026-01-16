"""
Report Generation Service
ADC 분석 결과 PDF/HTML 리포트 생성 및 캐싱

기능:
- Executive Summary 및 Pareto Front 기반 후보 요약
- 복합 캐시 키 (run_id + scoring/ruleset/template 버전) 기반 중복 생성 방지
- DB 유니크 인덱스를 활용한 동시성 제어 (Race Condition 방지)
- Supabase Storage 연동 및 Signed URL (7일 유효) 발급
- Cache-Control 최적화
"""

import os
import hashlib
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime
import structlog
from jinja2 import Environment, FileSystemLoader


logger = structlog.get_logger()


class ReportService:
    """리포트 생성 및 캐싱 서비스"""

    def __init__(self, db_client):
        self.db = db_client
        self.logger = logger.bind(service="report_service")
        # 템플릿 경로 설정
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "templates"
        )
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    async def generate_report_with_cache(
        self, run_id: UUID, versions: Dict[str, str]
    ) -> str:
        """캐시를 지원하는 리포트 생성 및 업로드"""
        # 1. 복합 캐시 키 생성
        cache_key_raw = f"{run_id}:{versions.get('scoring', 'v1')}:{versions.get('ruleset', 'v1')}:{versions.get('template', 'v1')}"
        cache_key = hashlib.sha256(cache_key_raw.encode()).hexdigest()

        self.logger.info(
            "report_generation_started", run_id=str(run_id), cache_key=cache_key
        )

        # 2. 캐시 확인
        cached = (
            await self.db.table("report_cache")
            .select("*")
            .eq("cache_key", cache_key)
            .execute()
        )
        if cached.data and cached.data[0].get("object_path"):
            self.logger.info("report_cache_hit", cache_key=cache_key)
            return await self._get_signed_url(cached.data[0]["object_path"])

        # 3. 동시성 제어 (선점 시도)
        try:
            await (
                self.db.table("report_cache")
                .insert(
                    {
                        "run_id": str(run_id),
                        "cache_key": cache_key,
                        "scoring_version": versions.get("scoring", "v1"),
                        "rule_set_version": versions.get("ruleset", "v1"),
                        "report_template_version": versions.get("template", "v1"),
                        "object_path": f"reports/{run_id}/{cache_key}.pdf",
                    }
                )
                .execute()
            )
        except Exception:
            # 이미 다른 프로세스가 생성 중이거나 완료함
            self.logger.info("report_cache_collision", cache_key=cache_key)
            # 잠시 대기 후 다시 조회
            cached = (
                await self.db.table("report_cache")
                .select("*")
                .eq("cache_key", cache_key)
                .execute()
            )
            if cached.data and cached.data[0].get("object_path"):
                return await self._get_signed_url(cached.data[0]["object_path"])

        # 4. 리포트 데이터 수집 및 생성
        run_data = await self._fetch_run_data(run_id)
        candidates = await self._fetch_top_candidates(run_id)
        evidence = await self._fetch_evidence(run_id)
        html_content = self._render_html(run_data, candidates, evidence)

        pdf_dir = "reports"
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f"report_{cache_key}.pdf")
        pdf_path = os.path.join(pdf_dir, f"report_{cache_key}.pdf")
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(pdf_path)

        # 5. Storage 업로드
        object_path = f"reports/{run_id}/{cache_key}.pdf"
        with open(pdf_path, "rb") as f:
            await self.db.storage.from_("reports").upload(
                path=object_path,
                file=f,
                file_options={"cache-control": "3600", "upsert": "true"},
            )

        # 6. 메타데이터 업데이트 (SHA256, Bytes 등)
        file_size = os.path.getsize(pdf_path)
        await (
            self.db.table("report_cache")
            .update({"bytes": file_size})
            .eq("cache_key", cache_key)
            .execute()
        )

        # 7. Signed URL 반환
        return await self._get_signed_url(object_path)

    async def _get_signed_url(self, object_path: str) -> str:
        """7일 유효한 서명된 URL 발급"""
        res = await self.db.storage.from_("reports").create_signed_url(
            object_path, 604800
        )
        return res["signedURL"]

    async def _fetch_run_data(self, run_id: UUID) -> Dict[str, Any]:
        res = (
            await self.db.table("design_runs")
            .select("*")
            .eq("id", str(run_id))
            .single()
            .execute()
        )
        return res.data

    async def _fetch_top_candidates(self, run_id: UUID) -> List[Dict[str, Any]]:
        res = (
            await self.db.table("run_pareto_members")
            .select("candidate_id, run_pareto_fronts!inner(front_index)")
            .eq("run_pareto_fronts.run_id", str(run_id))
            .eq("run_pareto_fronts.front_index", 0)
            .execute()
        )

        cand_ids = [m["candidate_id"] for m in res.data]
        if not cand_ids:
            return []

        cand_res = (
            await self.db.table("design_candidates")
            .select("*")
            .in_("id", cand_ids)
            .execute()
        )
        return cand_res.data

    async def _fetch_evidence(self, run_id: UUID) -> List[Dict[str, Any]]:
        res = (
            await self.db.table("evidence_signals")
            .select("*, design_candidates!inner(run_id)")
            .eq("design_candidates.run_id", str(run_id))
            .execute()
        )
        return res.data

    def _render_html(
        self,
        run_data: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
    ) -> str:
        template_str = """
        <html>
        <head>
            <style>
                body { font-family: 'NanumGothic', sans-serif; line-height: 1.6; color: #333; }
                .header { text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 20px; }
                .section { margin-top: 30px; }
                .candidate-card { border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
                .score { font-weight: bold; color: #2980b9; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ADC Design Analysis Report</h1>
                <p>Run ID: {{ run_id }} | Date: {{ date }}</p>
            </div>
            <div class="section">
                <h2>1. Executive Summary</h2>
                <p>Indication: {{ run_data.indication }}</p>
                <p>Status: Completed</p>
            </div>
            <div class="section">
                <h2>2. Top Candidates (Pareto Front 0)</h2>
                {% for cand in candidates %}
                <div class="candidate-card">
                    <h3>Candidate: {{ cand.id }}</h3>
                    <p>Target: {{ cand.target_id }} | Payload: {{ cand.payload_id }}</p>
                    <p>Total Score: <span class="score">{{ cand.total_score }}</span></p>
                </div>
                {% endfor %}
            </div>
            <div class="section">
                <h2>3. Evidence & Rationale</h2>
                <table>
                    <tr><th>Candidate</th><th>Signal Type</th><th>Content</th></tr>
                    {% for ev in evidence %}
                    <tr><td>{{ ev.candidate_id }}</td><td>{{ ev.signal_type }}</td><td>{{ ev.content }}</td></tr>
                    {% endfor %}
                </table>
            </div>
        </body>
        </html>
        """
        template = self.jinja_env.from_string(template_str)
        return template.render(
            run_id=run_data["id"],
            date=datetime.now().strftime("%Y-%m-%d"),
            run_data=run_data,
            candidates=candidates,
            evidence=evidence,
        )


def get_report_service(db_client) -> ReportService:
    return ReportService(db_client)
