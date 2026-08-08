export type StatementStatus =
  | "pending_review"
  | "urgent_escalation"
  | "reviewed"
  | "submitted"
  | "incomplete"
  | "archived";

export type InconsistencyCategory =
  | "temporal"
  | "identity"
  | "sequence"
  | "location"
  | "other";

export interface InconsistencyFlag {
  category: InconsistencyCategory | string;
  score: number;
  segment_a: string;
  segment_b: string;
  analysis?: string;
  legal_risk?: string;
  resolved?: boolean;
}

export interface ProtectionReferral {
  status: "none" | "referral_generated" | "submitted" | string;
  applicable_act?: string;
  grounds?: string[];
  province?: string;
  referral_pdf_url?: string;
}

export interface CoreFields {
  time_of_incident?: string;
  location?: string;
  persons_present?: string | string[];
  sequence_of_events?: string | string[];
  relationship_to_parties?: string;
}

export interface StatementSummary {
  ref_code: string;
  created_at: string;
  location?: string;
  status: StatementStatus | string;
  intimidation_flag?: boolean;
  inconsistency_flags?: InconsistencyFlag[];
  corroboration_score?: number | null;
  incident_cluster_id?: string | null;
  privacy_mode?: boolean;
  language_of_call?: string;
  witness_type?: string;
}

export interface StatementDetail extends StatementSummary {
  core_fields?: CoreFields;
  time_of_incident?: string;
  persons_present?: string | string[];
  sequence_of_events?: string | string[];
  relationship_to_parties?: string;
  raw_transcript?: string;
  readback_text?: string;
  readback_audio_url?: string | null;
  protection?: ProtectionReferral;
  protection_referral?: ProtectionReferral;
  corroboration_detail?: Record<string, unknown>;
  reviewer_notes?: string;
  reviewed_by?: string;
  reviewed_at?: string;
}

export interface StatementsResponse {
  items: StatementSummary[];
  total: number;
  page: number;
  page_size?: number;
}

export interface ReviewPayload {
  reviewer_notes: string;
  reviewed_by: string;
}

export interface SessionCreateResponse {
  token?: string;
  wsUrl?: string;
  ws_url?: string;
  roomName?: string;
  room_name?: string;
  [key: string]: unknown;
}

export interface FieldCorroboration {
  field: string;
  status: "agreement" | "partial" | "conflict" | "collusion_warning" | "single" | "insufficient_data" | string;
  agreement_score: number | null;
  values?: Array<{ ref_code?: string; value?: string } | string>;
  conflict_detail?: string;
  note?: string;
}

export interface ClusterSummary {
  id: string;
  cluster_label?: string;
  statement_count?: number;
  composite_score?: number | null;
  cluster_status?: string;
  incident_date_range?: string;
  created_at?: string;
  collusion_warning?: boolean;
}

export interface ClusterDetail extends ClusterSummary {
  field_results?: FieldCorroboration[];
  consensus_recommendation?: string;
  linked_statements?: StatementSummary[];
  statements?: StatementSummary[];
}

export interface KpiResponse {
  total_statements?: number;
  pending_review?: number;
  urgent?: number;
  clusters?: number;
  avg_corroboration?: number;
  [key: string]: unknown;
}

export interface HealthResponse {
  status: string;
  [key: string]: unknown;
}
