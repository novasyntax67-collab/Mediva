CREATE OR REPLACE FUNCTION public.has_break_glass(patient_profile_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM public.break_glass_events bge
        WHERE bge.actor_id = auth.uid()
          AND bge.patient_id = patient_profile_id
          AND bge.started_at <= now()
          AND (bge.ended_at IS NULL OR bge.ended_at > now())
          AND bge.started_at >= (now() - INTERVAL '15 minutes')
          AND bge.deleted_at IS NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public STABLE;
