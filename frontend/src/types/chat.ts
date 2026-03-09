export interface ConversationSummary {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview: string | null;
}

export interface MessageImage {
  id: number;
  filename: string;
  content_type: string;
  created_at: string;
}

export interface Message {
  id?: number;
  conversation_id: string;
  role: 'user' | 'assistant';
  content_text: string | null;
  content_structured: string | null;
  message_type: string;
  created_at: string;
  images: MessageImage[];
}

export interface ParsedProfile {
  failure_type: string;
  mce_bank: number | null;
  mce_code: string | null;
  mce_code_family: string | null;
  error_severity: string | null;
  thermal_state: string | null;
  voltage_state: string | null;
  boot_stage: string | null;
  frequency_context: string | null;
  failing_cores: string | null;
  raw_defect_type: string | null;
  keywords: string[];
  confidence: number;
  reasoning: string;
}

export interface RankedCommand {
  rank: number;
  command: string;
  confidence: number;
  fail_rate_on_similar: string | null;
  estimated_time_to_fail: string | null;
  reasoning: string | null;
  has_feedback?: boolean;
}

export interface PredictionData {
  analysis: {
    parsed_profile: ParsedProfile;
    match_tier: number;
    similar_parts_count: number;
    dominant_failure_pattern?: string;
    match_quality?: string;
  };
  commands: RankedCommand[];
  caveats: string[];
  fallback_suggestion?: string;
}

export interface SSEEvent {
  type: string;
  data: Record<string, unknown>;
}

export interface ThinkingStep {
  id: string;
  stage: PipelineStage;
  label: string;
  detail?: string;
  status: 'running' | 'done' | 'error';
  timestamp: number;
  data?: Record<string, unknown>;
}

export interface SearchCompleteData {
  tier: number;
  tier_description: string;
  count: number;
  num_commands: number;
  sources: string[];
  tool_distribution: Array<{
    tool: string;
    count: number;
    rate: number;
    sources: number;
    source_names: string[];
    details: string[];
    unique_cpus: number;
    banks: string[];
  }>;
  per_source_summary: Array<{
    source: string;
    record_count: number;
    tool_count: number;
  }>;
  sample_records: Array<{
    source: string;
    tool: string;
    count: number;
    bank?: string;
    unique_cpus?: number;
    defect_type?: string;
    uc_flag?: string;
  }>;
  formatted_command_table: string;
}

export type PipelineStage =
  | 'idle'
  | 'conversational'
  | 'chat_response'
  | 'parsing_started'
  | 'parsing_complete'
  | 'search_started'
  | 'search_complete'
  | 'ranking_started'
  | 'prediction'
  | 'done'
  | 'error';
