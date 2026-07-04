-- Enable RLS & Force RLS
ALTER TABLE public.appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.appointments FORCE ROW LEVEL SECURITY;

ALTER TABLE public.appointment_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.appointment_participants FORCE ROW LEVEL SECURITY;

-- Appointments SELECT Policy
CREATE POLICY appointments_select_policy ON public.appointments
FOR SELECT
TO authenticated
USING (
    is_patient(patient_id)
    OR doctor_id = auth.uid()
    OR is_patient_caregiver(patient_id)
    OR is_super_admin()
    OR EXISTS (
        SELECT 1 
        FROM public.clinics c 
        WHERE c.id = clinic_id 
          AND is_org_admin(c.organization_id)
    )
);

-- Appointments INSERT Policy
CREATE POLICY appointments_insert_policy ON public.appointments
FOR INSERT
TO authenticated
WITH CHECK (
    is_patient(patient_id)
    AND booked_by = auth.uid()
);

-- Appointments UPDATE Policy
CREATE POLICY appointments_update_policy ON public.appointments
FOR UPDATE
TO authenticated
USING (
    is_patient(patient_id)
    OR doctor_id = auth.uid()
    OR is_super_admin()
    OR EXISTS (
        SELECT 1 
        FROM public.clinics c 
        WHERE c.id = clinic_id 
          AND is_org_admin(c.organization_id)
    )
)
WITH CHECK (
    is_patient(patient_id)
    OR doctor_id = auth.uid()
    OR is_super_admin()
    OR EXISTS (
        SELECT 1 
        FROM public.clinics c 
        WHERE c.id = clinic_id 
          AND is_org_admin(c.organization_id)
    )
);

-- Appointment Participants SELECT Policy
CREATE POLICY appointment_participants_select_policy ON public.appointment_participants
FOR SELECT
TO authenticated
USING (
    profile_id = auth.uid()
    OR is_super_admin()
    OR EXISTS (
        SELECT 1 
        FROM public.appointments a 
        WHERE a.id = appointment_id 
          AND (is_patient(a.patient_id) OR a.doctor_id = auth.uid() OR is_patient_caregiver(a.patient_id))
    )
);
