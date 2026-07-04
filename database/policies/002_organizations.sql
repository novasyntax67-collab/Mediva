-- Enable RLS & Force RLS
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organizations FORCE ROW LEVEL SECURITY;

ALTER TABLE public.clinics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinics FORCE ROW LEVEL SECURITY;

ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_members FORCE ROW LEVEL SECURITY;

-- Organizations SELECT Policy
CREATE POLICY organizations_select_policy ON public.organizations
FOR SELECT
TO authenticated
USING (
    is_active_member(id)
    OR is_super_admin()
);

-- Clinics SELECT Policy
CREATE POLICY clinics_select_policy ON public.clinics
FOR SELECT
TO authenticated
USING (
    is_active_member(organization_id)
    OR is_super_admin()
);

-- Organization Members SELECT Policy
CREATE POLICY organization_members_select_policy ON public.organization_members
FOR SELECT
TO authenticated
USING (
    profile_id = auth.uid()
    OR is_super_admin()
    OR is_org_admin(organization_id)
    -- Clinicians can list members of their active organizations for care coordination
    OR (
        is_active_member(organization_id)
        AND EXISTS (
            SELECT 1 
            FROM public.profile_roles pr 
            JOIN public.roles r ON pr.role_id = r.id 
            WHERE pr.profile_id = auth.uid() 
              AND r.name = 'doctor'
        )
    )
);
