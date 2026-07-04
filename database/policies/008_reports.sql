-- Enable RLS & Force RLS
ALTER TABLE public.lab_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lab_orders FORCE ROW LEVEL SECURITY;

ALTER TABLE public.lab_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lab_results FORCE ROW LEVEL SECURITY;

ALTER TABLE public.lab_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lab_reports FORCE ROW LEVEL SECURITY;

ALTER TABLE public.radiology_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.radiology_reports FORCE ROW LEVEL SECURITY;

ALTER TABLE public.medical_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medical_documents FORCE ROW LEVEL SECURITY;

ALTER TABLE public.attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attachments FORCE ROW LEVEL SECURITY;

-- Lab Orders SELECT Policy
CREATE POLICY lab_orders_select_policy ON public.lab_orders
FOR SELECT
TO authenticated
USING (
    is_patient(patient_id)
    OR is_assigned_doctor(patient_id)
    OR is_patient_caregiver(patient_id)
    OR has_break_glass(patient_id)
    OR is_super_admin()
);

-- Lab Results SELECT Policy
CREATE POLICY lab_results_select_policy ON public.lab_results
FOR SELECT
TO authenticated
USING (
    is_super_admin()
    OR EXISTS (
        SELECT 1 
        FROM public.lab_orders o
        WHERE o.id = lab_order_id
    )
);

-- Lab Reports SELECT Policy
CREATE POLICY lab_reports_select_policy ON public.lab_reports
FOR SELECT
TO authenticated
USING (
    is_patient(patient_id)
    OR is_assigned_doctor(patient_id)
    OR is_patient_caregiver(patient_id)
    OR has_break_glass(patient_id)
    OR is_super_admin()
);

-- Radiology Reports SELECT Policy
CREATE POLICY radiology_reports_select_policy ON public.radiology_reports
FOR SELECT
TO authenticated
USING (
    is_patient(patient_id)
    OR is_assigned_doctor(patient_id)
    OR is_patient_caregiver(patient_id)
    OR has_break_glass(patient_id)
    OR is_super_admin()
);

-- Medical Documents SELECT Policy
CREATE POLICY medical_documents_select_policy ON public.medical_documents
FOR SELECT
TO authenticated
USING (
    is_patient(patient_id)
    OR is_assigned_doctor(patient_id)
    OR is_patient_caregiver(patient_id)
    OR has_break_glass(patient_id)
    OR is_super_admin()
);

-- Attachments SELECT Policy
CREATE POLICY attachments_select_policy ON public.attachments
FOR SELECT
TO authenticated
USING (
    is_super_admin()
    OR (associated_type = 'lab_report' AND EXISTS (
        SELECT 1 FROM public.lab_reports r WHERE r.id = associated_id
    ))
    OR (associated_type = 'radiology_report' AND EXISTS (
        SELECT 1 FROM public.radiology_reports r WHERE r.id = associated_id
    ))
    OR (associated_type = 'consultation' AND EXISTS (
        SELECT 1 FROM public.consultations c WHERE c.appointment_id = associated_id
    ))
);
