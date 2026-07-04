import { createClient } from '@supabase/supabase-js';

export const initSupabaseClient = (url: string, anonKey: string) => {
  return createClient(url, anonKey);
};

export type SupabaseClientType = ReturnType<typeof initSupabaseClient>;
