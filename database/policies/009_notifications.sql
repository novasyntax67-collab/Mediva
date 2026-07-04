-- Enable RLS & Force RLS
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications FORCE ROW LEVEL SECURITY;

ALTER TABLE public.notification_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_deliveries FORCE ROW LEVEL SECURITY;

-- Notifications SELECT Policy
CREATE POLICY notifications_select_policy ON public.notifications
FOR SELECT
TO authenticated
USING (
    recipient_id = auth.uid()
    OR is_super_admin()
);

-- Notification Deliveries SELECT Policy
CREATE POLICY notification_deliveries_select_policy ON public.notification_deliveries
FOR SELECT
TO authenticated
USING (
    is_super_admin()
    OR EXISTS (
        SELECT 1 
        FROM public.notifications n
        WHERE n.id = notification_id
          AND n.recipient_id = auth.uid()
    )
);
