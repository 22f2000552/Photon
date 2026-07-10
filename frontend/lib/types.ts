export interface Requirement {
  id: number;
  raw_text: string;
  product: string;
  grade: string;
  quantity: number | null;
  unit: string;
  location: string;
  deadline: string | null;
  budget_amount: number | null;
  budget_basis: string;
  certifications: string[];
  delivery_terms: string;
  parse_confidence: number;
  parse_source: string;
}

export interface Contact {
  id: number;
  channel: string;
  value: string;
  is_preferred: boolean;
  verified: boolean;
}

export interface Certificate {
  id: number;
  cert_type: string;
  number: string;
  issued_by: string;
  valid_till: string | null;
  status: string;
}

export interface Memory {
  avg_response_hours: number | null;
  response_rate: number;
  on_time_rate: number;
  ghost_count: number;
  doc_quality: number;
  reliability_score: number;
  rfq_count: number;
}

export interface ReliabilityEvent {
  id: number;
  event_type: string;
  detail: string;
  impact: number;
  rfq_id: number | null;
  created_at: string;
}

export interface Vendor {
  id: number;
  name: string;
  city: string;
  state: string;
  gst_number: string;
  categories: string[];
  notes: string;
  profile_completeness: number;
  contacts: Contact[];
  certificates: Certificate[];
  memory: Memory | null;
  events?: ReliabilityEvent[];
}

export interface ScoutCandidate {
  vendor_id: number;
  name: string;
  city: string;
  channels: string[];
  certificates: { type: string; number: string; status: string }[];
  profile_completeness: number;
  flags: string[];
  reliability_score: number;
  past_rfqs: number;
  qualified: boolean;
}

export interface RFQMessage {
  id: number;
  vendor_id: number;
  direction: string;
  channel: string;
  body: string;
  status: string;
  meta: Record<string, unknown>;
  created_at: string;
}

export interface ParsedItem {
  field: string;
  value: string;
  confidence: number;
  evidence: string;
}

export interface Quote {
  id: number;
  vendor_id: number;
  raw_text: string;
  price: number | null;
  unit_basis: string;
  delivery_included: boolean | null;
  gst_included: boolean | null;
  freight_included: boolean | null;
  delivery_days: number | null;
  delivery_date: string | null;
  delivery_vague: boolean;
  cert_attached: boolean;
  confidence: number;
  flags: string[];
  normalized_price: number | null;
  normalized_basis: string;
  normalization_notes: string[];
  price_score: number | null;
  delivery_score: number | null;
  doc_score: number | null;
  reliability_score: number | null;
  overall_score: number | null;
  rank: number | null;
  score_evidence: Record<string, string>;
  items: ParsedItem[];
}

export interface ShortlistEntry {
  rank: number;
  vendor_id: number;
  vendor_name: string;
  city: string;
  quote_id: number;
  normalized_price: number | null;
  normalized_basis: string;
  overall_score: number;
  scores: { price: number; delivery: number; docs: number; reliability: number };
  reasons: string[];
  risks: string[];
}

export interface RFQSummary {
  id: number;
  status: string;
  created_at: string;
  requirement: Requirement;
  quote_count: number;
  contacted_count: number;
}

export interface RFQDetail {
  id: number;
  status: string;
  created_at: string;
  requirement: Requirement;
  scout_result: ScoutCandidate[];
  shortlist: ShortlistEntry[];
  explanation: string;
  messages: RFQMessage[];
  quotes: Quote[];
  vendors: Vendor[];
}