CREATE OR REPLACE FUNCTION public.is_patient(patient_profile_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN auth.uid() = patient_profile_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public STABLE;

CREATE OR REPLACE FUNCTION public.is_assigned_doctor(patient_profile_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if primary doctor
    IF EXISTS (
        SELECT 1
        FROM public.patients p
        WHERE p.id = patient_profile_id
          AND p.primary_doctor_id = auth.uid()
          AND p.deleted_at IS NULL
    ) THEN
        RETURN TRUE;
    END IF;

    -- Check if has an active appointment
    RETURN EXISTS (
        SELECT 1
        FROM public.appointments a
        WHERE a.patient_id = patient_profile_id
          AND a.doctor_id = auth.uid()
          AND a.status IN ('scheduled', 'confirmed', 'checked_in')
          AND a.deleted_at IS NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public STABLE;

CREATE OR REPLACE FUNCTION public.is_patient_caregiver(patient_profile_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Verify caregiver assignment is active and approved
    IF NOT EXISTS (
        SELECT 1
        FROM public.caregiver_assignments ca
        WHERE ca.patient_id = patient_profile_id
          AND ca.caregiver_id = auth.uid()
          AND ca.approved_by_patient = TRUE
          AND ca.deleted_at IS NULL
    ) THEN
        RETURN FALSE;
    END IF;

    -- Verify active non-revoked consent exists
    RETURN EXISTS (
        SELECT 1
        FROM public.consent_grants cg
        WHERE cg.patient_id = patient_profile_id
          AND cg.granted_to = auth.uid()
          AND cg.revoked_at IS NULL
          AND (cg.expires_at IS NULL OR cg.expires_at > now())
          AND cg.deleted_at IS NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public STABLE;
