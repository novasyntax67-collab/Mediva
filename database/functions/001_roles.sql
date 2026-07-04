CREATE OR REPLACE FUNCTION public.is_super_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 
        FROM public.profile_roles pr
        JOIN public.roles r ON pr.role_id = r.id
        WHERE pr.profile_id = auth.uid() 
          AND r.name = 'super_admin'
          AND pr.deleted_at IS NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public STABLE;

CREATE OR REPLACE FUNCTION public.is_org_admin(target_org_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 
        FROM public.profile_roles pr
        JOIN public.roles r ON pr.role_id = r.id
        JOIN public.organization_members om ON pr.profile_id = om.profile_id
        WHERE pr.profile_id = auth.uid() 
          AND om.organization_id = target_org_id
          AND r.name = 'org_admin'
          AND om.status = 'active'
          AND pr.deleted_at IS NULL
          AND om.deleted_at IS NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public STABLE;
