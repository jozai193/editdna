export type Word = { word: string; start: number; end: number };
export type Segment = {
  id: string;
  start: number;
  end: number;
  text?: string;
  locked?: boolean;
};
export type Asset = {
  id: string;
  name: string;
  role: string;
  duration: number;
  peaks: number[];
  words: Word[];
  provenance?: string;
};
export type Match = {
  id: string;
  final_start: number;
  final_end: number;
  raw_start: number;
  raw_end: number;
  score: number;
  status: string;
  alternatives: { start: number; score: number }[];
};
export type Pair = {
  visual?: {
    observations: {
      match_id: string;
      status: string;
      zoom?: number;
      reason?: string;
      raw_time: number;
      final_time: number;
    }[];
  };
  id: string;
  name: string;
  profile_id: string;
  raw_id: string;
  final_id: string;
  revision: number;
  alignment?: { matches: Match[]; coverage: number };
};
export type Evidence = {
  pair_id: string;
  raw_pause: number;
  kept_pause: number;
};
export type Version = {
  visual?: {
    status: string;
    zoom?: number;
    session_count: number;
    reason?: string;
  };
  id: string;
  profile_id: string;
  number: number;
  pause_seconds: number;
  session_count: number;
  observation_count: number;
  confidence: string;
  unknown: string[];
  evidence: Evidence[];
  take_preference?: 'first' | 'last';
  take_evidence?: { pair_id: string }[];
};
export type Decision = {
  id: string;
  kind: string;
  start: number;
  end: number;
  removed: number;
  reason: string;
  origin: string;
};
export type Plan = {
  visual?: { zoom: number; origin: string; session_count?: number };
  id: string;
  asset_id: string;
  profile_version_id: string | null;
  revision: number;
  mode: string;
  duration: number;
  source_duration: number;
  segments: Segment[];
  decisions: Decision[];
  history: Segment[][];
  take_preference?: string;
};
export type Export = {
  id: string;
  plan_id: string;
  revision: number;
  duration: number;
  has_captions: boolean;
};
export type Job = { id: string; task: string; status: string; message: string };
export type EvaluationResult = {
  framing_zoom?: number;
  framing_error?: number;
  profile: string;
  session: number;
  split: string;
  personalized_error_ms: number;
  generic_error_ms: number;
  take_agreement_pct: number;
};
export type Evaluation = {
  status: string;
  training_sessions: number;
  held_out_sessions: number;
  alignment_precision_pct: number;
  correspondence_median_ms: number;
  summary: string;
  limitations: string;
  results: EvaluationResult[];
};
export type State = {
  assets: Asset[];
  profiles: { id: string; name: string }[];
  pairs: Pair[];
  versions: Version[];
  plans: Plan[];
  exports: Export[];
  jobs: Job[];
};
export type MutationResult = { id: string; status?: string; detail?: string };
