export type LayerId = "opinion_shift" | "chronicle" | "constellation" | "lab";

export type ShiftId =
  | "republic_shift"
  | "ecological_shift"
  | "science_shift"
  | "political_shift";

export type ShiftPhase = "before" | "after";

export interface DatasetTag {
  label: string;
  slug: string;
  domain: "sociology" | "policy" | "anthropology" | "cross_cutting";
  method: "manual" | "llm_map" | "hybrid" | "keyword";
  confidence: number;
}

export interface RawArticleRecord {
  id: number;
  article_uid?: string;
  external_id: string | null;
  title: string;
  date_iso: string;
  year: number;
  url: string | null;
  has_source_url: boolean;
  publication: string;
  section: string;
  reading_minutes: number | null;
  summary: string | null;
  tone: string | null;
  status: "draft" | "verified" | "published";
  summary_method: string;
  retrieval_method: string;
  text_state?: "missing" | "partial" | "full";
  has_full_text?: boolean;
  tags: DatasetTag[];
  shift_annotations?: Partial<Record<ShiftId, PersistedShiftAnnotation>>;
  republic_critical?: RepublicCriticalAnalysis;
}

export interface PersistedShiftAnnotation {
  phase: ShiftPhase;
  connection: string;
  key_message: string;
  audit: {
    method: string;
    version: string;
    input_fingerprint: string;
    run_uid: string;
    generated_at: string;
    provenance_note: string | null;
  };
}

export interface RepublicCriticalAnalysis {
  phase: ShiftPhase;
  include_in_story: boolean;
  relevance_score: number;
  strength_label: "strong" | "moderate" | "weak";
  connection_text: string;
  rationale: string;
  quote_text: string;
  quote_source: "body_paragraph" | "summary_sentence" | "title";
  quote_confidence: number;
  audit: {
    method: string;
    version: string;
    input_fingerprint: string;
    run_uid: string;
    generated_at: string;
  };
}

export interface DatasetMetadata {
  project: string;
  dataset: string;
  generated_at_utc: string;
  database_mode?: string;
  article_count: number;
  verified_count: number;
  source_url_count: number;
  full_text_count?: number;
  shift_annotation_count?: number;
  republic_annotation_count?: number;
  republic_curated_count?: number;
  year_range: number[];
  years: number[];
  publications?: Array<{
    name: string;
    count: number;
  }>;
  tones: string[];
  sections: string[];
  tags: Array<{
    label: string;
    slug: string;
    domain: DatasetTag["domain"];
    count: number;
  }>;
}

export interface DatasetPayload {
  metadata: DatasetMetadata;
  articles: RawArticleRecord[];
}

export interface ShiftContext {
  shift_id: ShiftId;
  phase: ShiftPhase;
  narrative_note: string;
  key_message: string;
}

export interface ShiftProjectionRecord {
  article_id: string;
  meta: {
    year: number;
    title: string;
    date_iso: string;
    url: string | null;
    publication: string;
    section: string;
    reading_minutes: number | null;
  };
  analysis: {
    summary: string | null;
    tone: string | null;
    tags: DatasetTag[];
  };
  shift_context: ShiftContext;
  score: number;
}

export interface ShiftDefinition {
  id: ShiftId;
  label: string;
  milestoneYear: number;
  fromStatement: string;
  toStatement: string;
  changeSummary: string;
  keywords: string[];
  preferredTagSlugs: string[];
  beforeNarrative: string;
  afterNarrative: string;
}

export interface FilterState {
  searchTerm: string;
  year: "all" | number;
}

export interface EngineState {
  activeView: LayerId;
  activeShift: ShiftId;
  activeFilter: FilterState;
}

export interface ShiftSplitResult {
  definition: ShiftDefinition;
  before: ShiftProjectionRecord[];
  after: ShiftProjectionRecord[];
  total: number;
}
