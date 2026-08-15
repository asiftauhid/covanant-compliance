import type {
  Borrower,
  ChatMessage,
  ChatTurnResult,
  HealthResponse,
  LoanAnalysisResult,
  TableData,
  TableSummary,
} from "./types";

// Empty string must not win over the default (?? only treats null/undefined).
const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(
  /\/$/,
  "",
);

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_URL}${path}`;
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch {
    throw new Error(
      `Could not reach the API at ${API_URL}. If this is the hosted UI, set NEXT_PUBLIC_API_URL to your Render URL (no trailing slash) and redeploy.`,
    );
  }

  if (!response.ok) {
    let detail = response.statusText || "Request failed";
    try {
      const payload = await response.json();
      if (typeof payload.detail === "string") {
        detail = payload.detail;
      } else if (payload.detail) {
        detail = JSON.stringify(payload.detail);
      }
    } catch {
      // Non-JSON error body; keep the status text.
    }
    throw new Error(`${response.status} ${detail} — ${url}`);
  }

  return response.json() as Promise<T>;
}

export function fetchHealth() {
  return request<HealthResponse>("/health");
}

export function fetchBorrowers() {
  return request<Borrower[]>("/borrowers");
}

export function fetchTables() {
  return request<TableSummary[]>("/tables");
}

export function fetchTableRows(name: string) {
  return request<TableData>(`/tables/${name}`);
}

export function analyzeLoanAgreement(
  file: File,
  borrowerId: string,
  period: string,
) {
  const body = new FormData();
  body.append("file", file);
  body.append("borrower_id", borrowerId);
  body.append("period", period);

  return request<LoanAnalysisResult>("/covenants/analyze", {
    method: "POST",
    body,
  });
}

export function chatWithData(question: string, history: ChatMessage[]) {
  return request<ChatTurnResult>("/chatwithdata", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
  });
}

export { API_URL };
