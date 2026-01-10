-- 사용자 데이터 업로드 테이블 (MVP)
-- 참고: 개발구현기획안_사용자업로드.md

-- === 1. uploads 테이블 ===
CREATE TABLE IF NOT EXISTS public.uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id UUID NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('candidate_csv', 'experiment_csv', 'doc_pdf')),
    filename TEXT NOT NULL,
    storage_bucket TEXT NOT NULL DEFAULT 'user-uploads',
    storage_key TEXT NOT NULL,
    mime_type TEXT,
    size_bytes BIGINT,
    checksum TEXT,
    status TEXT NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'parsing', 'parsed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- uploads 인덱스
CREATE INDEX IF NOT EXISTS idx_uploads_owner ON public.uploads(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_uploads_status ON public.uploads(status);

-- === 2. user_candidates 테이블 (사용자 개인 후보) ===
CREATE TABLE IF NOT EXISTS public.user_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id UUID NOT NULL,
    name TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    features JSONB DEFAULT '{}',
    source_upload_id UUID REFERENCES public.uploads(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- user_candidates 인덱스
CREATE INDEX IF NOT EXISTS idx_user_candidates_owner ON public.user_candidates(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_user_candidates_source ON public.user_candidates(source_upload_id);

-- === 3. candidate_inputs 테이블 (원본 행 저장) ===
CREATE TABLE IF NOT EXISTS public.candidate_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES public.user_candidates(id) ON DELETE CASCADE,
    owner_user_id UUID NOT NULL,
    raw_row JSONB NOT NULL,
    row_index INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- candidate_inputs 인덱스
CREATE INDEX IF NOT EXISTS idx_candidate_inputs_candidate ON public.candidate_inputs(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_inputs_owner ON public.candidate_inputs(owner_user_id);

-- === 4. RLS 정책 ===
ALTER TABLE public.uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidate_inputs ENABLE ROW LEVEL SECURITY;

-- uploads RLS
CREATE POLICY "Users can view own uploads"
    ON public.uploads FOR SELECT
    USING (owner_user_id = auth.uid());

CREATE POLICY "Users can insert own uploads"
    ON public.uploads FOR INSERT
    WITH CHECK (owner_user_id = auth.uid());

CREATE POLICY "Users can update own uploads"
    ON public.uploads FOR UPDATE
    USING (owner_user_id = auth.uid());

CREATE POLICY "Users can delete own uploads"
    ON public.uploads FOR DELETE
    USING (owner_user_id = auth.uid());

-- user_candidates RLS
CREATE POLICY "Users can view own candidates"
    ON public.user_candidates FOR SELECT
    USING (owner_user_id = auth.uid());

CREATE POLICY "Users can insert own candidates"
    ON public.user_candidates FOR INSERT
    WITH CHECK (owner_user_id = auth.uid());

CREATE POLICY "Users can update own candidates"
    ON public.user_candidates FOR UPDATE
    USING (owner_user_id = auth.uid());

CREATE POLICY "Users can delete own candidates"
    ON public.user_candidates FOR DELETE
    USING (owner_user_id = auth.uid());

-- candidate_inputs RLS
CREATE POLICY "Users can view own inputs"
    ON public.candidate_inputs FOR SELECT
    USING (owner_user_id = auth.uid());

CREATE POLICY "Users can insert own inputs"
    ON public.candidate_inputs FOR INSERT
    WITH CHECK (owner_user_id = auth.uid());

CREATE POLICY "Users can delete own inputs"
    ON public.candidate_inputs FOR DELETE
    USING (owner_user_id = auth.uid());

-- === 5. Service Role bypass (for backend API) ===
-- Service role key를 사용하는 백엔드는 RLS를 우회함

-- === 6. updated_at 트리거 ===
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_uploads_updated_at
    BEFORE UPDATE ON public.uploads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_candidates_updated_at
    BEFORE UPDATE ON public.user_candidates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
