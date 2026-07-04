-- Enable RLS & Force RLS
ALTER TABLE public.measurement_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.measurement_types FORCE ROW LEVEL SECURITY;

ALTER TABLE public.vitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vitals FORCE ROW LEVEL SECURITY;

ALTER TABLE public.devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.devices FORCE ROW LEVEL SECURITY;

ALTER TABLE public.device_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.device_assignments FORCE ROW LEVEL SECURITY;

-- Measurement Types SELECT Policy
CREATE POLICY measurement_types_select_policy ON public.measurement_types
FOR SELECT
TO authenticated
USING (true);

-- Measurement Types WRITE Policy
CREATE POLICY measurement_types_write_policy ON public.measurement_types
FOR ALL
TO authenticated
USING (is_super_admin())
WITH CHECK (is_super_admin());

-- Vitals SELECT Policy
CREATE POLICY vitals_select_policy ON public.vitals
FOR SELECT
TO authenticated
USING (
    is_patient(patient_id)
    OR is_assigned_doctor(patient_id)
    OR is_patient_caregiver(patient_id)
    OR has_break_glass(patient_id)
    OR is_super_admin()
);

-- Vitals INSERT Policy
CREATE POLICY vitals_insert_policy ON public.vitals
FOR INSERT
TO authenticated
WITH CHECK (
    is_patient(patient_id)
    OR is_assigned_doctor(patient_id)
    OR is_super_admin()
);

-- Devices SELECT Policy
CREATE POLICY devices_select_policy ON public.devices
FOR SELECT
TO authenticated
USING (
    owner_id = auth.uid()
    OR is_super_admin()
    OR is_org_admin(organization_id)
);

-- Device Assignments SELECT Policy
CREATE POLICY device_assignments_select_policy ON public.device_assignments
FOR SELECT
TO authenticated
USING (
    is_patient(patient_id)
    OR is_super_admin()
    OR EXISTS (
        SELECT 1 
        FROM public.devices d 
        WHERE d.id = device_id 
          AND is_org_admin(d.organization_id)
    )
);
