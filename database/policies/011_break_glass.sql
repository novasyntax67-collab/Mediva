-- Enable RLS & Force RLS
ALTER TABLE public.break_glass_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.break_glass_events FORCE ROW LEVEL SECURITY;

-- Break Glass Events SELECT Policy
CREATE POLICY break_glass_events_select_policy ON public.break_glass_events
FOR SELECT
TO authenticated
USING (
    actor_id = auth.uid()
    OR is_super_admin()
);

-- Break Glass Events INSERT Policy
CREATE POLICY break_glass_events_insert_policy ON public.break_glass_events
FOR INSERT
TO authenticated
WITH CHECK (
    actor_id = auth.uid()
    AND length(trim(reason)) > 0
    AND length(trim(justification)) > 0
);
