-- Enable RLS & Force RLS
ALTER TABLE public.patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patients FORCE ROW LEVEL SECURITY;

ALTER TABLE public.patient_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_contacts FORCE ROW LEVEL SECURITY;

ALTER TABLE public.caregiver_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.caregiver_assignments FORCE ROW LEVEL SECURITY;

-- Patients SELECT Policy
CREATE POLICY patients_select_policy ON public.patients
FOR SELECT
TO authenticated
USING (
    is_patient(id)
    OR is_assigned_doctor(id)
    OR is_patient_caregiver(id)
    OR has_break_glass(id)
    OR is_super_admin()
    OR is_org_admin(organization_id)
);

-- Patients UPDATE Policy
CREATE POLICY patients_update_policy ON public.patients
FOR UPDATE
TO authenticated
USING (
    is_patient(id)
    OR is_assigned_doctor(id)
    OR is_super_admin()
    OR is_org_admin(organization_id)
)
WITH CHECK (
    is_patient(id)
    OR is_assigned_doctor(id)
    OR is_super_admin()
    OR is_org_admin(organization_id)
);

-- Patient Contacts SELECT Policy
CREATE POLICY patient_contacts_select_policy ON public.patient_contacts
FOR SELECT
TO authenticated
USING (
    is_patient(patient_id)
    OR is_assigned_doctor(patient_id)
    OR is_patient_caregiver(patient_id)
    OR has_break_glass(patient_id)
    OR is_super_admin()
);

-- Patient Contacts UPDATE Policy
CREATE POLICY patient_contacts_update_policy ON public.patient_contacts
FOR UPDATE
TO authenticated
USING (
    is_patient(patient_id)
    OR is_super_admin()
)
WITH CHECK (
    is_patient(patient_id)
    OR is_super_admin()
);

-- Caregiver Assignments SELECT Policy
CREATE POLICY caregiver_assignments_select_policy ON public.caregiver_assignments
FOR SELECT
TO authenticated
USING (
    is_patient(patient_id)
    OR caregiver_id = auth.uid()
    OR is_super_admin()
);

-- Caregiver Assignments UPDATE Policy
CREATE POLICY caregiver_assignments_update_policy ON public.caregiver_assignments
FOR UPDATE
TO authenticated
USING (
    is_patient(patient_id)
    OR is_super_admin()
)
WITH CHECK (
    is_patient(patient_id)
    OR is_super_admin()
);
