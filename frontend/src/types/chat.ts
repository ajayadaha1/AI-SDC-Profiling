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
  error_severity: string | null;
  thermal_state: string | null;
  boot_stage: string | null;
  confidence: number;
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
