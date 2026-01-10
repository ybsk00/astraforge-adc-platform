-- ================================================
-- Migration 006: Add Vector Search Function
-- Description: RPC function for similarity search on literature_chunks
-- ================================================

-- Function to match literature chunks by embedding similarity
CREATE OR REPLACE FUNCTION public.match_literature_chunks (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  content text,
  similarity float,
  document_title text,
  document_authors jsonb,
  document_year date
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    lc.id,
    lc.document_id,
    lc.content,
    1 - (lc.embedding <=> query_embedding) as similarity,
    ld.title as document_title,
    ld.authors as document_authors,
    ld.publication_date as document_year
  FROM public.literature_chunks lc
  JOIN public.literature_documents ld ON lc.document_id = ld.id
  WHERE 1 - (lc.embedding <=> query_embedding) > match_threshold
  ORDER BY lc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
