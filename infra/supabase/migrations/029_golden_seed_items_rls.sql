-- ================================================
-- Migration 029: Add RLS write policies for golden_seed_items
-- Description: Allow authenticated users to update golden_seed_items
-- ================================================

-- Update policy (인증된 사용자가 update 가능)
CREATE POLICY "Authenticated users can update golden_seed_items" 
    ON public.golden_seed_items 
    FOR UPDATE 
    TO authenticated 
    USING (true)
    WITH CHECK (true);

-- Insert policy (인증된 사용자가 insert 가능)
CREATE POLICY "Authenticated users can insert golden_seed_items" 
    ON public.golden_seed_items 
    FOR INSERT 
    TO authenticated 
    WITH CHECK (true);

-- Notify PostgREST to reload schema cache
NOTIFY pgrst, 'reload config';
