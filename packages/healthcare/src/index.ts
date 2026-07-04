export interface FHIRPatient {
  resourceType: 'Patient';
  id: string;
  name: Array<{
    use?: string;
    family: string;
    given: string[];
  }>;
  gender?: 'male' | 'female' | 'other' | 'unknown';
  birthDate?: string;
}

export function parseFHIRPatient(fhirPatient: FHIRPatient) {
  const primaryName = fhirPatient.name[0];
  const firstName = primaryName?.given?.join(' ') || '';
  const lastName = primaryName?.family || '';
  
  return {
    id: fhirPatient.id,
    fullName: `${firstName} ${lastName}`.trim(),
    gender: fhirPatient.gender,
    dateOfBirth: fhirPatient.birthDate,
  };
}
