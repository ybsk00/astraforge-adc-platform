-- =====================================================
-- ADC Platform - 추가 DDL (Readiness Checklist 보완)
-- Version: 1.0
-- Date: 2026-01-08
-- =====================================================

-- =====================================================
-- 1. run_progress (런 진행률 추적)
-- Checklist §5.5
-- =====================================================
CREATE TABLE IF NOT EXISTS run_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES design_runs(id) ON DELETE CASCADE,
    
    -- 진행 상태
    phase TEXT NOT NULL,  -- 'generating' | 'scoring' | 'pareto' | 'evidence' | 'protocol' | 'completed' | 'failed'
    phase_order INTEGER NOT NULL DEFAULT 0,  -- 단계 순서 (1, 2, 3, ...)
    
    -- 진행률
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    progress_pct DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE WHEN total_items > 0 
            THEN ROUND((processed_items::DECIMAL / total_items) * 100, 2) 
            ELSE 0 
        END
    ) STORED,
    
    -- 메타
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    meta JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_run_progress_run_id ON run_progress(run_id);
CREATE INDEX IF NOT EXISTS idx_run_progress_phase ON run_progress(phase);

-- RLS (워크스페이스 격리)
ALTER TABLE run_progress ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE run_progress IS '런 진행률 추적 테이블 (Checklist §5.5)';

-- =====================================================
-- 2. audit_events (감사 로그)
-- Checklist §5.11
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 이벤트 정보
    event_type TEXT NOT NULL,  -- 'run.created' | 'run.completed' | 'ruleset.changed' | 'catalog.updated' | 'export.created'
    event_category TEXT NOT NULL,  -- 'run' | 'catalog' | 'ruleset' | 'export' | 'literature' | 'auth'
    
    -- 대상 정보
    resource_type TEXT,  -- 'design_run' | 'component' | 'ruleset' | 'scoring_params' | 'literature_document'
    resource_id TEXT,  -- UUID 또는 버전 문자열
    
    -- 액터 정보
    user_id UUID,  -- 사용자 ID (NULL이면 시스템)
    workspace_id UUID,  -- 워크스페이스 ID
    actor_type TEXT DEFAULT 'user',  -- 'user' | 'system' | 'worker'
    
    -- 상세
    action TEXT NOT NULL,  -- 'create' | 'update' | 'delete' | 'execute' | 'export'
    description TEXT,
    old_value JSONB,  -- 변경 전 값 (민감 정보 마스킹)
    new_value JSONB,  -- 변경 후 값 (민감 정보 마스킹)
    meta JSONB DEFAULT '{}'::jsonb,
    
    -- IP/요청 정보
    ip_address INET,
    user_agent TEXT,
    request_id TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_audit_events_event_type ON audit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_events_event_category ON audit_events(event_category);
CREATE INDEX IF NOT EXISTS idx_audit_events_resource ON audit_events(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_workspace_id ON audit_events(workspace_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at DESC);

-- 파티셔닝 권장 (대용량 시)
-- 보존 정책: 1년 (별도 스케줄러로 삭제)

COMMENT ON TABLE audit_events IS '감사 이벤트 로그 (Checklist §5.11) - 1년 보관';

-- =====================================================
-- 3. evidence_signals (문헌 polarity 태그)
-- Checklist §4.4, §5.5
-- =====================================================
CREATE TABLE IF NOT EXISTS evidence_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES literature_chunks(id) ON DELETE CASCADE,
    
    -- Polarity
    polarity TEXT NOT NULL CHECK (polarity IN ('positive', 'negative', 'neutral')),
    confidence DECIMAL(3, 2) DEFAULT 0.5,  -- 0.00 ~ 1.00
    
    -- 분류 정보
    signal_type TEXT,  -- 'efficacy' | 'toxicity' | 'stability' | 'cmc' | 'clinical'
    keywords TEXT[],  -- 추출된 키워드
    
    -- 메타
    detector TEXT,  -- 'rule' | 'llm' | 'manual'
    detector_version TEXT,
    meta JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(chunk_id)  -- 청크당 1개 시그널
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_evidence_signals_chunk_id ON evidence_signals(chunk_id);
CREATE INDEX IF NOT EXISTS idx_evidence_signals_polarity ON evidence_signals(polarity);
CREATE INDEX IF NOT EXISTS idx_evidence_signals_signal_type ON evidence_signals(signal_type);

COMMENT ON TABLE evidence_signals IS '문헌 청크 polarity 태그 (Checklist §4.4)';

-- =====================================================
-- 4. 기존 테이블 보완 (컬럼 추가)
-- =====================================================

-- design_runs에 scoring_version 컬럼 추가 (없는 경우)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'design_runs' AND column_name = 'scoring_version'
    ) THEN
        ALTER TABLE design_runs ADD COLUMN scoring_version TEXT DEFAULT 'v0.2';
    END IF;
END $$;

-- literature_chunks에 polarity 컬럼 추가 (간단 버전)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'literature_chunks' AND column_name = 'polarity'
    ) THEN
        ALTER TABLE literature_chunks ADD COLUMN polarity TEXT DEFAULT 'neutral';
    END IF;
END $$;



-- =====================================================
-- 완료 메시지
-- =====================================================
SELECT 'DDL Migration Complete: run_progress, audit_events, evidence_signals' AS status;
