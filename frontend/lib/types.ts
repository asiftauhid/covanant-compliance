export type ComplianceStatus =
  | "compliant"
  | "warning"
  | "breached"
  | "insufficient_data"
  | "manual_review";

export interface Borrower {
  id: string;
  name: string;
  industry: string;
}

export interface TableSummary {
  name: string;
  row_count: number;
  columns: string[];
}

export type Cell = string | number | boolean | null;

export interface TableData {
  table: string;
  columns: string[];
  rows: Record<string, Cell>[];
}

export interface CovenantRule {
  name: string;
  metric: string;
  operator: string;
  threshold: number;
  currency?: string | null;
  frequency?: string | null;
  source_text: string;
  calculation_request?: string | null;
}

export interface EvaluationResult {
  name: string;
  metric: string;
  source_text: string;
  operator: string;
  threshold: number;
  actual: number | null;
  status: ComplianceStatus;
  inputs: Record<string, number>;
  currency?: string | null;
  difference?: number | null;
  reason?: string | null;
}

export interface RetrievalResult {
  intent: string;
  sql?: string | null;
  rows: Record<string, Cell>[];
  inference_ms: number;
  model?: string | null;
  error?: string | null;
}

export interface CovenantAnalysisItem {
  covenant: CovenantRule;
  intent: string;
  check: {
    retrieval: RetrievalResult;
    evaluation: EvaluationResult;
  };
}

export interface LoanAnalysisResult {
  borrower_id: string;
  period: string;
  extraction: {
    covenants: CovenantRule[];
    text_chars: number;
    inference_ms: number;
    model: string;
    error?: string | null;
  };
  results: CovenantAnalysisItem[];
}

export interface HealthResponse {
  status: string;
  llm_provider: string;
  model: string;
  endpoint: string;
}
