export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface AIStatusResponse {
  llm: { endpoint: string; model: string; configured: boolean };
  vision: { endpoint: string; model: string; configured: boolean };
  snowflake: { configured: boolean; account: string };
  embedding: { model: string; dimensions: number };
}

export interface FeedbackSubmission {
  prediction_command_id: number;
  actual_result: 'FAIL' | 'PASS' | 'NOT_RUN';
  notes?: string;
  submitted_by?: string;
}
