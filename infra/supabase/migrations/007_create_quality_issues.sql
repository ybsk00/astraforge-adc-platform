-- ================================================
-- Migration: Create Quality Issues Table
-- ================================================

CREATE TABLE IF NOT EXISTS public.quality_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL CHECK (type IN ('conflict', 'outdated', 'retracted', 'missing_citation')),
    description TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('high', 'medium', 'low')),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'ignored')),
    evidence_id TEXT, -- Can be linked to literature_chunks or external ID
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_quality_issues_status ON public.quality_issues(status);
CREATE INDEX IF NOT EXISTS idx_quality_issues_type ON public.quality_issues(type);

-- RLS
ALTER TABLE public.quality_issues ENABLE ROW LEVEL SECURITY;

-- Policies (Simple: Authenticated users can view/update)
CREATE POLICY "Authenticated users can view quality issues"
    ON public.quality_issues FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can insert quality issues"
    ON public.quality_issues FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can update quality issues"
    ON public.quality_issues FOR UPDATE
    USING (auth.role() = 'authenticated');

-- Trigger for updated_at
CREATE TRIGGER update_quality_issues_updated_at
    BEFORE UPDATE ON public.quality_issues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
