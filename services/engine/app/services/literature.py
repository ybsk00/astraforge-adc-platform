"""
Literature Chunking and Embedding Service
문헌 청킹 + OpenAI 임베딩

체크리스트 §5.8, §6 기반
"""

import os
import re
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class Chunk:
    """문헌 청크"""

    document_id: str
    chunk_index: int
    content: str
    token_count: int
    checksum: str
    section: Optional[str] = None
    polarity: Optional[str] = None  # positive, negative, neutral


class ChunkingService:
    """
    문헌 청킹 서비스

    권장: 300-800 tokens per chunk
    """

    DEFAULT_MIN_TOKENS = 300
    DEFAULT_MAX_TOKENS = 800
    DEFAULT_OVERLAP_TOKENS = 50

    def __init__(
        self, min_tokens: int = None, max_tokens: int = None, overlap_tokens: int = None
    ):
        self.min_tokens = min_tokens or self.DEFAULT_MIN_TOKENS
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        self.overlap_tokens = overlap_tokens or self.DEFAULT_OVERLAP_TOKENS
        self.logger = logger.bind(service="chunking")

    def chunk_document(
        self,
        document_id: str,
        title: str,
        abstract: str,
        full_text: str = None,
        metadata: Dict[str, Any] = None,
    ) -> List[Chunk]:
        """
        문서를 청크로 분할

        Args:
            document_id: 문서 ID
            title: 제목
            abstract: 초록
            full_text: 전문 (optional)
            metadata: 추가 메타데이터

        Returns:
            List of Chunk objects
        """
        chunks = []
        chunk_index = 0

        # 1. Title + Abstract 청크 (항상 포함)
        title_abstract = f"Title: {title}\n\nAbstract: {abstract}"
        title_chunks = self._split_text(title_abstract, "title_abstract")

        for text in title_chunks:
            chunks.append(
                self._create_chunk(document_id, chunk_index, text, "abstract")
            )
            chunk_index += 1

        # 2. Full text 청크 (있으면)
        if full_text:
            sections = self._extract_sections(full_text)

            for section_name, section_text in sections.items():
                section_chunks = self._split_text(section_text, section_name)

                for text in section_chunks:
                    chunks.append(
                        self._create_chunk(document_id, chunk_index, text, section_name)
                    )
                    chunk_index += 1

        self.logger.info(
            "document_chunked", document_id=document_id, chunk_count=len(chunks)
        )

        return chunks

    def _split_text(self, text: str, section: str = None) -> List[str]:
        """텍스트를 적절한 크기로 분할"""
        if not text:
            return []

        # 간단한 토큰 수 추정 (단어 기반)
        words = text.split()

        if len(words) <= self.max_tokens:
            return [text]

        chunks = []
        current_start = 0

        while current_start < len(words):
            # 최대 토큰 수만큼 가져오기
            end = min(current_start + self.max_tokens, len(words))

            # 문장 경계 찾기
            chunk_words = words[current_start:end]
            chunk_text = " ".join(chunk_words)

            # 문장 끝에서 자르기 시도
            if end < len(words):
                last_period = chunk_text.rfind(". ")
                if last_period > len(chunk_text) // 2:
                    chunk_text = chunk_text[: last_period + 1]
                    end = current_start + len(chunk_text.split())

            chunks.append(chunk_text)

            # 오버랩 적용
            current_start = end - self.overlap_tokens
            if current_start <= end - self.max_tokens:
                current_start = end

        return chunks

    def _extract_sections(self, full_text: str) -> Dict[str, str]:
        """전문에서 섹션 추출"""
        sections = {}

        # 일반적인 논문 섹션 패턴
        section_patterns = [
            (r"\bintroduction\b", "introduction"),
            (r"\bmethods?\b", "methods"),
            (r"\bresults?\b", "results"),
            (r"\bdiscussion\b", "discussion"),
            (r"\bconclusion\b", "conclusion"),
            (r"\breferences?\b", "references"),
        ]

        # 섹션 분리 시도
        current_section = "body"
        sections[current_section] = []

        for line in full_text.split("\n"):
            line_lower = line.lower().strip()

            for pattern, section_name in section_patterns:
                if re.search(pattern, line_lower):
                    current_section = section_name
                    if current_section not in sections:
                        sections[current_section] = []
                    break

            if current_section != "references":  # 참고문헌 제외
                if isinstance(sections[current_section], list):
                    sections[current_section].append(line)

        # 리스트를 텍스트로 결합
        return {k: "\n".join(v) for k, v in sections.items() if v}

    def _create_chunk(
        self, document_id: str, chunk_index: int, content: str, section: str
    ) -> Chunk:
        """청크 객체 생성"""
        token_count = len(content.split())
        checksum = hashlib.md5(content.encode()).hexdigest()[:16]

        return Chunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            token_count=token_count,
            checksum=checksum,
            section=section,
            polarity=None,  # 나중에 분류
        )

    def detect_polarity(self, chunk: Chunk) -> str:
        """
        청크의 극성 감지 (positive/negative/neutral)

        간단한 키워드 기반 (나중에 NLI로 고도화)
        """
        content_lower = chunk.content.lower()

        # Negative 신호
        negative_keywords = [
            "failed",
            "failure",
            "discontinued",
            "terminated",
            "toxicity",
            "adverse",
            "death",
            "mortality",
            "withdrew",
            "withdrawn",
            "ineffective",
            "no significant",
            "did not show",
        ]

        # Positive 신호
        positive_keywords = [
            "effective",
            "success",
            "approved",
            "improved",
            "benefit",
            "significant improvement",
            "response rate",
            "well tolerated",
        ]

        neg_count = sum(1 for kw in negative_keywords if kw in content_lower)
        pos_count = sum(1 for kw in positive_keywords if kw in content_lower)

        if neg_count > pos_count:
            return "negative"
        elif pos_count > neg_count:
            return "positive"
        else:
            return "neutral"


class EmbeddingService:
    """
    OpenAI 임베딩 서비스

    기본 모델: text-embedding-3-small
    """

    DEFAULT_MODEL = "text-embedding-3-small"
    BATCH_SIZE = 100  # OpenAI 배치 제한

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or self.DEFAULT_MODEL
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.logger = logger.bind(service="embedding")

        if not self.api_key:
            self.logger.warning("openai_api_key_not_set")

    async def embed_text(self, text: str) -> List[float]:
        """단일 텍스트 임베딩"""
        embeddings = await self.embed_batch([text])
        return embeddings[0] if embeddings else []

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """배치 임베딩"""
        if not self.api_key:
            self.logger.warning("skipping_embed_no_api_key")
            return [[] for _ in texts]

        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)

            all_embeddings = []

            for i in range(0, len(texts), self.BATCH_SIZE):
                batch = texts[i : i + self.BATCH_SIZE]

                response = client.embeddings.create(model=self.model, input=batch)

                # 정렬된 순서로 반환
                batch_embeddings = [None] * len(batch)
                for item in response.data:
                    batch_embeddings[item.index] = item.embedding

                all_embeddings.extend(batch_embeddings)

            self.logger.info("batch_embedded", count=len(texts), model=self.model)

            return all_embeddings

        except Exception as e:
            self.logger.error("embedding_failed", error=str(e))
            return [[] for _ in texts]

    async def embed_chunks(self, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """
        청크 목록 임베딩

        Returns:
            [{"chunk_id": ..., "embedding": [...], ...}, ...]
        """
        texts = [c.content for c in chunks]
        embeddings = await self.embed_batch(texts)

        results = []
        for chunk, embedding in zip(chunks, embeddings):
            results.append(
                {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "token_count": chunk.token_count,
                    "checksum": chunk.checksum,
                    "section": chunk.section,
                    "polarity": chunk.polarity,
                    "embedding": embedding,
                }
            )

        return results


class LiteraturePipeline:
    """
    문헌 처리 파이프라인

    문서 → 청킹 → 극성 감지 → 임베딩 → DB 저장
    """

    def __init__(self, db_client=None):
        self.db = db_client
        self.chunking = ChunkingService()
        self.embedding = EmbeddingService()
        self.logger = logger.bind(service="literature_pipeline")

    async def process_document(
        self,
        document_id: str,
        title: str,
        abstract: str,
        full_text: str = None,
        workspace_id: str = None,
    ) -> Dict[str, Any]:
        """
        문서 처리 파이프라인

        Returns:
            {"chunks_created": N, "chunks_embedded": N}
        """
        stats = {"chunks_created": 0, "chunks_embedded": 0, "errors": 0}

        try:
            # 1. 청킹
            chunks = self.chunking.chunk_document(
                document_id, title, abstract, full_text
            )
            stats["chunks_created"] = len(chunks)

            # 2. 극성 감지
            for chunk in chunks:
                chunk.polarity = self.chunking.detect_polarity(chunk)

            # 3. 임베딩
            embedded_chunks = await self.embedding.embed_chunks(chunks)
            stats["chunks_embedded"] = sum(
                1 for c in embedded_chunks if c.get("embedding")
            )

            # 4. DB 저장
            if self.db:
                for chunk_data in embedded_chunks:
                    try:
                        self.db.table("literature_chunks").upsert(
                            {
                                "document_id": chunk_data["document_id"],
                                "chunk_index": chunk_data["chunk_index"],
                                "content": chunk_data["content"],
                                "token_count": chunk_data["token_count"],
                                "section": chunk_data["section"],
                                "polarity": chunk_data.get("polarity"),
                                "embedding": chunk_data.get("embedding"),
                                "checksum": chunk_data["checksum"],
                            },
                            on_conflict="document_id,chunk_index",
                        ).execute()
                    except Exception as e:
                        self.logger.warning("chunk_save_failed", error=str(e))
                        stats["errors"] += 1

            self.logger.info("document_processed", document_id=document_id, stats=stats)

        except Exception as e:
            self.logger.error("pipeline_failed", error=str(e))
            stats["errors"] += 1

        return stats

    async def process_batch(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        배치 문서 처리

        Args:
            documents: [{"id": ..., "title": ..., "abstract": ...}, ...]
        """
        total_stats = {
            "documents": len(documents),
            "chunks_created": 0,
            "chunks_embedded": 0,
            "errors": 0,
        }

        for doc in documents:
            stats = await self.process_document(
                document_id=doc.get("id"),
                title=doc.get("title", ""),
                abstract=doc.get("abstract", ""),
                full_text=doc.get("full_text"),
                workspace_id=doc.get("workspace_id"),
            )

            total_stats["chunks_created"] += stats.get("chunks_created", 0)
            total_stats["chunks_embedded"] += stats.get("chunks_embedded", 0)
            total_stats["errors"] += stats.get("errors", 0)

        return total_stats


# 편의 함수
def get_chunking_service() -> ChunkingService:
    return ChunkingService()


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


def get_literature_pipeline(db_client=None) -> LiteraturePipeline:
    return LiteraturePipeline(db_client)
