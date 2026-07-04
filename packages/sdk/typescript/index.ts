export interface ClientConfig {
  baseUrl: string;
}

export class MedivaSDK {
  constructor(private config: ClientConfig) {}

  async getPatients() {
    const res = await fetch(`${this.config.baseUrl}/api/v1/patients`);
    return res.json();
  }
}
