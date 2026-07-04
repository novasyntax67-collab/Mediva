-- Enable RLS & Force RLS
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs FORCE ROW LEVEL SECURITY;

-- Audit Logs SELECT Policy
CREATE POLICY audit_logs_select_policy ON public.audit_logs
FOR SELECT
TO authenticated
USING (
    is_super_admin()
);
