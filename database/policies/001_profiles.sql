-- Enable RLS & Force RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles FORCE ROW LEVEL SECURITY;

ALTER TABLE public.profile_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_roles FORCE ROW LEVEL SECURITY;

-- Profiles SELECT Policy
CREATE POLICY profiles_select_policy ON public.profiles
FOR SELECT
TO authenticated
USING (
    id = auth.uid()
    OR is_super_admin()
    OR is_assigned_doctor(id)
    OR is_patient_caregiver(id)
    OR EXISTS (
        SELECT 1 
        FROM public.organization_members om 
        WHERE om.profile_id = id 
          AND is_org_admin(om.organization_id)
    )
);

-- Profiles UPDATE Policy
CREATE POLICY profiles_update_policy ON public.profiles
FOR UPDATE
TO authenticated
USING (id = auth.uid())
WITH CHECK (id = auth.uid());

-- Profile Roles SELECT Policy
CREATE POLICY profile_roles_select_policy ON public.profile_roles
FOR SELECT
TO authenticated
USING (
    profile_id = auth.uid()
    OR is_super_admin()
    OR EXISTS (
        SELECT 1 
        FROM public.organization_members om 
        WHERE om.profile_id = profile_id 
          AND is_org_admin(om.organization_id)
    )
);
