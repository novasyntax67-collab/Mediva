-- Enable RLS & Force RLS
ALTER TABLE public.medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medications FORCE ROW LEVEL SECURITY;

ALTER TABLE public.prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prescriptions FORCE ROW LEVEL SECURITY;

ALTER TABLE public.prescription_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prescription_items FORCE ROW LEVEL SECURITY;

ALTER TABLE public.medication_adherence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medication_adherence FORCE ROW LEVEL SECURITY;

-- Medications SELECT Policy
CREATE POLICY medications_select_policy ON public.medications
FOR SELECT
TO authenticated
USING (true);

-- Medications WRITE Policy
CREATE POLICY medications_write_policy ON public.medications
FOR ALL
TO authenticated
USING (is_super_admin())
WITH CHECK (is_super_admin());

-- Prescriptions SELECT Policy
CREATE POLICY prescriptions_select_policy ON public.prescriptions
FOR SELECT
TO authenticated
USING (
    is_patient(patient_id)
    OR is_assigned_doctor(patient_id)
    OR is_patient_caregiver(patient_id)
    OR has_break_glass(patient_id)
    OR is_super_admin()
);

-- Prescriptions WRITE Policy
CREATE POLICY prescriptions_write_policy ON public.prescriptions
FOR ALL
TO authenticated
USING (
    is_assigned_doctor(patient_id)
    OR is_super_admin()
)
WITH CHECK (
    is_assigned_doctor(patient_id)
    OR is_super_admin()
);

-- Prescription Items SELECT Policy
CREATE POLICY prescription_items_select_policy ON public.prescription_items
FOR SELECT
TO authenticated
USING (
    is_super_admin()
    OR EXISTS (
        SELECT 1 
        FROM public.prescriptions p
        WHERE p.id = prescription_id
    )
);

-- Medication Adherence SELECT Policy
CREATE POLICY medication_adherence_select_policy ON public.medication_adherence
FOR SELECT
TO authenticated
USING (
    is_patient(patient_id)
    OR is_assigned_doctor(patient_id)
    OR is_patient_caregiver(patient_id)
    OR has_break_glass(patient_id)
    OR is_super_admin()
);

-- Medication Adherence UPDATE Policy
CREATE POLICY medication_adherence_update_policy ON public.medication_adherence
FOR UPDATE
TO authenticated
USING (
    is_patient(patient_id)
    OR is_patient_caregiver(patient_id)
    OR is_super_admin()
)
WITH CHECK (
    is_patient(patient_id)
    OR is_patient_caregiver(patient_id)
    OR is_super_admin()
);
