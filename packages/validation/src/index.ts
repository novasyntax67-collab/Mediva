import { z } from 'zod';

export const UserRoleSchema = z.enum(['patient', 'clinician', 'caregiver', 'admin']);

export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: UserRoleSchema,
});

export const VitalSignInputSchema = z.object({
  patientId: z.string().uuid(),
  type: z.enum(['heart_rate', 'blood_pressure', 'spo2', 'temperature', 'glucose']),
  value: z.number().positive(),
  timestamp: z.string().datetime().optional(),
});
