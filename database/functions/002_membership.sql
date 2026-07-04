CREATE OR REPLACE FUNCTION public.is_active_member(target_org_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM public.organization_members om
        WHERE om.profile_id = auth.uid()
          AND om.organization_id = target_org_id
          AND om.status = 'active'
          AND om.deleted_at IS NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public STABLE;
