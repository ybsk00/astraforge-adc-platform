"""
Evidence RAG Service
Forced Evidence 규격 기반 근거 생성

체크리스트 §4.2, §8.2 기반:
- Forced Evidence: 인용 없으면 "Assumption" 라벨링
- Conflict Alert: 찬성/반대 근거 동시 존재 시
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class Citation:
    """인용 정보"""

    pmid: Optional[str] = None
    doi: Optional[str] = None
    title: str = ""
    text_span: str = ""
    relevance_score: float = 0.0
    polarity: str = "neutral"  # positive, negative, neutral


@dataclass
class EvidenceResult:
    """근거 생성 결과"""

    claim: str
    evidence_text: str
    citations: List[Citation] = field(default_factory=list)
    has_evidence: bool = False
    is_assumption: bool = True
    conflict_alert: bool = False
    conflict_reason: Optional[str] = None
    confidence_score: float = 0.0


class EvidenceRAGService:
    """
    Evidence RAG 서비스

    Forced Evidence 규격:
    - 모든 주장에 대해 문헌 인용 필요
    - 인용 없으면 "Assumption" 라벨
    - 찬성/반대 근거 동시 존재 시 Conflict Alert
    """

    MIN_CITATIONS = 2  # 최소 인용 수
    CONFLICT_THRESHOLD = 0.3  # Conflict 판단 임계값

    def __init__(self, db_client=None, llm_client=None):
        self.db = db_client
        self.llm = llm_client
        self.logger = logger.bind(service="evidence_rag")

    async def generate_evidence(
        self,
        candidate: Dict[str, Any],
        score_components: Dict[str, Any],
        top_k: int = 10,
    ) -> EvidenceResult:
        """
        후보에 대한 근거 생성

        Args:
            candidate: 후보 정보 (target, payload, etc.)
            score_components: 스코어 컴포넌트
            top_k: 검색할 문헌 수

        Returns:
            EvidenceResult
        """
        result = EvidenceResult(claim="", evidence_text="", is_assumption=True)

        try:
            # 1. 검색 쿼리 생성
            query = self._build_search_query(candidate, score_components)
            result.claim = query

            # 2. 문헌 검색 (하이브리드: 벡터 + 키워드)
            relevant_chunks = await self._search_literature(query, top_k)

            if not relevant_chunks:
                result.evidence_text = "[Assumption] No literature evidence found."
                result.is_assumption = True
                return result

            # 3. Risk-first retrieval: negative polarity 부스팅
            risk_fields = self._get_high_risk_fields(score_components)
            if risk_fields:
                # Negative polarity 청크 우선
                relevant_chunks = self._boost_negative_polarity(
                    relevant_chunks, risk_fields
                )

            # 4. 인용 추출
            citations = self._extract_citations(relevant_chunks)
            result.citations = citations
            result.has_evidence = len(citations) >= 1
            result.is_assumption = len(citations) < self.MIN_CITATIONS

            # 5. Conflict Alert 체크
            conflict, reason = self._check_conflict(citations)
            result.conflict_alert = conflict
            result.conflict_reason = reason

            # 6. 근거 텍스트 생성 (LLM)
            evidence_text = await self._generate_evidence_text(
                candidate, citations, result.is_assumption
            )
            result.evidence_text = evidence_text

            # 7. 신뢰도 점수
            result.confidence_score = self._calculate_confidence(
                len(citations), conflict, result.is_assumption
            )

            self.logger.info(
                "evidence_generated",
                citations=len(citations),
                has_evidence=result.has_evidence,
                conflict=result.conflict_alert,
            )

        except Exception as e:
            self.logger.error("evidence_generation_failed", error=str(e))
            result.evidence_text = f"[Assumption] Evidence generation failed: {str(e)}"

        return result

    def _build_search_query(
        self, candidate: Dict[str, Any], score_components: Dict[str, Any]
    ) -> str:
        """검색 쿼리 생성"""
        parts = []

        # Target name
        target = candidate.get("target", {})
        target_name = target.get("name") or target.get("gene_symbol", "")
        if target_name:
            parts.append(target_name)

        # Payload class
        payload = candidate.get("payload", {})
        payload_class = payload.get("payload_class", "")
        if payload_class:
            parts.append(payload_class)

        # ADC context
        parts.append("ADC antibody drug conjugate")

        # High risk fields
        if score_components:
            for fit_type in ["bio_fit", "safety_fit", "eng_fit"]:
                terms = score_components.get(fit_type, {}).get("terms", {})
                for term_name, value in terms.items():
                    if value > 30:  # High risk
                        parts.append(term_name)

        return " ".join(parts)

    async def _search_literature(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """문헌 검색 (하이브리드)"""
        if not self.db:
            return []

        try:
            # 키워드 검색 (tsvector)
            keyword_result = (
                self.db.table("literature_chunks")
                .select("*, literature_documents(pmid, title)")
                .text_search("tsvector_content", query)
                .limit(top_k // 2)
                .execute()
            )

            # 벡터 검색 (embedding) - TODO: 임베딩 쿼리
            # 현재는 키워드 검색만 사용

            return keyword_result.data if keyword_result.data else []

        except Exception as e:
            self.logger.warning("literature_search_failed", error=str(e))
            return []

    def _get_high_risk_fields(self, score_components: Dict[str, Any]) -> List[str]:
        """고위험 필드 추출"""
        high_risk = []

        for fit_type in ["bio_fit", "safety_fit", "eng_fit"]:
            terms = score_components.get(fit_type, {}).get("terms", {})
            for term_name, value in terms.items():
                if value > 30:
                    high_risk.append(term_name)

        return high_risk

    def _boost_negative_polarity(
        self, chunks: List[Dict[str, Any]], risk_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """Negative polarity 청크 부스팅"""

        def rank(chunk):
            score = 0
            if chunk.get("polarity") == "negative":
                score += 10
            if chunk.get("polarity") == "positive":
                score -= 5
            # Risk field 관련 키워드 포함 시 부스팅
            content = chunk.get("content", "").lower()
            for risk_field in risk_fields:
                if risk_field.lower() in content:
                    score += 5
            return score

        return sorted(chunks, key=rank, reverse=True)

    def _extract_citations(self, chunks: List[Dict[str, Any]]) -> List[Citation]:
        """청크에서 인용 추출"""
        citations = []
        seen_pmids = set()

        for chunk in chunks:
            doc = chunk.get("literature_documents", {})
            pmid = doc.get("pmid")

            if pmid and pmid not in seen_pmids:
                seen_pmids.add(pmid)

                citations.append(
                    Citation(
                        pmid=pmid,
                        title=doc.get("title", ""),
                        text_span=chunk.get("content", "")[:500],
                        relevance_score=chunk.get("relevance_score", 0.5),
                        polarity=chunk.get("polarity", "neutral"),
                    )
                )

        return citations

    def _check_conflict(self, citations: List[Citation]) -> tuple[bool, Optional[str]]:
        """
        Conflict Alert 체크

        조건:
        - 찬성/반대 근거 동시 존재
        - 인용 수 < 2 + 불확실성 높음
        """
        polarities = [c.polarity for c in citations]
        pos_count = polarities.count("positive")
        neg_count = polarities.count("negative")

        # 찬성/반대 동시 존재
        if pos_count > 0 and neg_count > 0:
            ratio = min(pos_count, neg_count) / max(pos_count, neg_count, 1)
            if ratio > self.CONFLICT_THRESHOLD:
                return (
                    True,
                    f"Conflicting evidence: {pos_count} positive, {neg_count} negative citations",
                )

        # 인용 수 부족
        if len(citations) < self.MIN_CITATIONS:
            return True, f"Insufficient citations: only {len(citations)} sources found"

        return False, None

    async def _generate_evidence_text(
        self, candidate: Dict[str, Any], citations: List[Citation], is_assumption: bool
    ) -> str:
        """LLM을 사용한 근거 텍스트 생성"""
        prefix = "[Assumption] " if is_assumption else ""

        if not citations:
            return f"{prefix}No literature evidence available for this candidate."

        # 간단한 요약 생성 (LLM 없이)
        target_name = candidate.get("target", {}).get("name", "target")
        citation_texts = []

        for i, cit in enumerate(citations[:5], 1):
            polarity_marker = ""
            if cit.polarity == "positive":
                polarity_marker = "✅"
            elif cit.polarity == "negative":
                polarity_marker = "⚠️"

            citation_texts.append(
                f"{i}. {polarity_marker} [{cit.pmid}] {cit.title[:100]}..."
            )

        evidence = f"{prefix}Evidence for {target_name} based on {len(citations)} publications:\n\n"
        evidence += "\n".join(citation_texts)

        # TODO: Gemini API로 세부 요약 생성

        return evidence

    def _calculate_confidence(
        self, citation_count: int, has_conflict: bool, is_assumption: bool
    ) -> float:
        """신뢰도 점수 계산"""
        score = 0.5

        # 인용 수에 따라 증가
        score += min(0.3, citation_count * 0.05)

        # Conflict 시 감소
        if has_conflict:
            score -= 0.2

        # Assumption 시 감소
        if is_assumption:
            score -= 0.3

        return max(0.0, min(1.0, score))

    def to_db_format(self, candidate_id: str, result: EvidenceResult) -> Dict[str, Any]:
        """DB 저장 형식 변환"""
        return {
            "candidate_id": candidate_id,
            "evidence_text": result.evidence_text,
            "citations": [
                {
                    "pmid": c.pmid,
                    "title": c.title,
                    "text_span": c.text_span,
                    "polarity": c.polarity,
                }
                for c in result.citations
            ],
            "has_evidence": result.has_evidence,
            "is_assumption": result.is_assumption,
            "conflict_alert": result.conflict_alert,
            "conflict_reason": result.conflict_reason,
            "confidence_score": result.confidence_score,
        }


# 편의 함수
def get_evidence_service(db_client=None) -> EvidenceRAGService:
    return EvidenceRAGService(db_client)
