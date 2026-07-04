-- Enable RLS & Force RLS
ALTER TABLE public.consultations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consultations FORCE ROW LEVEL SECURITY;

ALTER TABLE public.consultation_diagnoses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consultation_diagnoses FORCE ROW LEVEL SECURITY;

-- Consultations SELECT Policy
CREATE POLICY consultations_select_policy ON public.consultations
FOR SELECT
TO authenticated
USING (
    is_super_admin()
    OR EXISTS (
        SELECT 1 
        FROM public.appointments a 
        WHERE a.id = appointment_id 
          AND (is_patient(a.patient_id) OR a.doctor_id = auth.uid() OR is_patient_caregiver(a.patient_id) OR has_break_glass(a.patient_id))
    )
);

-- Consultations UPDATE Policy
CREATE POLICY consultations_update_policy ON public.consultations
FOR UPDATE
TO authenticated
USING (
    (
        is_super_admin()
        OR EXISTS (
            SELECT 1 
            FROM public.appointments a 
            WHERE a.id = appointment_id 
              AND (a.doctor_id = auth.uid() OR has_break_glass(a.patient_id))
        )
    )
    -- Enforce immutability of completed consultations at the database layer
    AND status != 'completed'
)
WITH CHECK (
    status != 'completed'
);

-- Consultation Diagnoses SELECT Policy
CREATE POLICY consultation_diagnoses_select_policy ON public.consultation_diagnoses
FOR SELECT
TO authenticated
USING (
    is_super_admin()
    OR EXISTS (
        SELECT 1 
        FROM public.consultations c
        WHERE c.appointment_id = consultation_id
    )
);
