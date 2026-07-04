export interface User {
  id: string;
  email: string;
  role: 'patient' | 'clinician' | 'caregiver' | 'admin';
}

export interface Patient extends User {
  dateOfBirth?: string;
  gender?: string;
  vitals?: VitalSign[];
}

export interface VitalSign {
  id: string;
  patientId: string;
  timestamp: string;
  type: 'heart_rate' | 'blood_pressure' | 'spo2' | 'temperature' | 'glucose';
  value: number;
}
