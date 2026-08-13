"use client";

import { useEffect, useState } from "react";

import { analyzeLoanAgreement, fetchBorrowers } from "@/lib/api";
import type {
  Borrower,
  ComplianceStatus,
  CovenantAnalysisItem,
  LoanAnalysisResult,
} from "@/lib/types";

const STATUS_TEXT: Record<ComplianceStatus, string> = {
  compliant: "text-emerald-700",
  warning: "text-amber-700",
  breached: "text-red-700",
  insufficient_data: "text-neutral-500",
  manual_review: "text-neutral-500",
};

const STATUS_BORDER: Record<ComplianceStatus, string> = {
  compliant: "border-l-emerald-600",
  warning: "border-l-amber-500",
  breached: "border-l-red-600",
  insufficient_data: "border-l-neutral-300",
  manual_review: "border-l-neutral-300",
};

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return Number.isInteger(value) ? value.toLocaleString() : String(value);
}

function CovenantResult({ item }: { item: CovenantAnalysisItem }) {
  const { evaluation, retrieval } = item.check;

  return (
    <li className={`border-l-2 bg-white px-3 py-2.5 ${STATUS_BORDER[evaluation.status]}`}>
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-[13px] text-neutral-900">{evaluation.name}</span>
        <span className={`text-[12px] ${STATUS_TEXT[evaluation.status]}`}>
          {evaluation.status.replace("_", " ")}
        </span>
      </div>

      <p className="mt-1 text-[12px] text-neutral-600 tabular-nums">
        {evaluation.metric} {evaluation.operator} {formatNumber(evaluation.threshold)}
        <span className="mx-1.5 text-neutral-300">|</span>
        actual {formatNumber(evaluation.actual)}
        {evaluation.difference !== null && evaluation.difference !== undefined && (
          <span className="ml-1.5 text-neutral-400">
            ({evaluation.difference > 0 ? "+" : ""}
            {formatNumber(evaluation.difference)})
          </span>
        )}
      </p>

      {evaluation.reason && (
        <p className="mt-1 text-[12px] text-neutral-500">{evaluation.reason}</p>
      )}

      <details className="mt-1.5 text-[12px]">
        <summary className="cursor-pointer text-neutral-400 hover:text-neutral-700">
          audit trail
        </summary>
        <div className="mt-2 space-y-2 text-neutral-600">
          <p className="border-l border-neutral-200 pl-2 italic">
            {evaluation.source_text}
          </p>
          {Object.keys(evaluation.inputs).length > 0 && (
            <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
              {Object.entries(evaluation.inputs).map(([name, value]) => (
                <div key={name} className="col-span-2 flex justify-between gap-4">
                  <dt className="text-neutral-500">{name}</dt>
                  <dd className="tabular-nums">{value.toLocaleString()}</dd>
                </div>
              ))}
            </dl>
          )}
          {retrieval.sql && (
            <pre className="overflow-x-auto whitespace-pre-wrap break-words bg-neutral-50 p-2 font-mono text-[11px] text-neutral-700">
              {retrieval.sql}
            </pre>
          )}
          <p className="text-neutral-400">
            sql generated in {retrieval.inference_ms}ms
            {retrieval.model ? ` · ${retrieval.model}` : ""}
          </p>
        </div>
      </details>
    </li>
  );
}

export default function CompliancePanel() {
  const [borrowers, setBorrowers] = useState<Borrower[]>([]);
  const [borrowerId, setBorrowerId] = useState("");
  const [period, setPeriod] = useState("2026-07");
  const [file, setFile] = useState<File | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LoanAnalysisResult | null>(null);

  useEffect(() => {
    fetchBorrowers()
      .then((rows) => {
        setBorrowers(rows);
        setBorrowerId((current) => current || rows[0]?.id || "");
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;

    setRunning(true);
    setError(null);
    setResult(null);

    try {
      setResult(await analyzeLoanAgreement(file, borrowerId, period));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-neutral-50">
      <form
        onSubmit={handleSubmit}
        className="shrink-0 border-b border-neutral-200 bg-white px-4 py-3"
      >
        <div className="max-w-md space-y-2.5">
          <label className="block text-[12px] text-neutral-500">
            Loan agreement
            <input
              type="file"
              accept="application/pdf"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="mt-1 block w-full cursor-pointer border border-neutral-200 px-2 py-1.5 text-[12px] text-neutral-700 file:mr-2 file:border-0 file:bg-transparent file:p-0 file:text-[12px] file:text-neutral-500"
            />
          </label>

          <div className="flex gap-2">
            <label className="flex-1 text-[12px] text-neutral-500">
              Borrower
              <select
                value={borrowerId}
                onChange={(event) => setBorrowerId(event.target.value)}
                className="mt-1 block w-full border border-neutral-200 bg-white px-2 py-1.5 text-[12px] text-neutral-800"
              >
                {borrowers.map((borrower) => (
                  <option key={borrower.id} value={borrower.id}>
                    {borrower.id} · {borrower.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="w-28 text-[12px] text-neutral-500">
              Period
              <input
                value={period}
                onChange={(event) => setPeriod(event.target.value)}
                placeholder="2026-07"
                className="mt-1 block w-full border border-neutral-200 px-2 py-1.5 text-[12px] tabular-nums text-neutral-800"
              />
            </label>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={running || !file || !borrowerId}
              className="bg-neutral-900 px-3 py-1.5 text-[12px] text-white hover:bg-neutral-700 disabled:bg-neutral-300"
            >
              {running ? "Running…" : "Run check"}
            </button>
            <a
              href="/loan_agreement_sample.pdf"
              className="text-[12px] text-neutral-400 underline underline-offset-2 hover:text-neutral-700"
            >
              sample pdf
            </a>
          </div>
        </div>
      </form>

      {error && (
        <p className="border-b border-red-100 bg-red-50 px-4 py-2 text-[12px] text-red-700">
          {error}
        </p>
      )}

      <div className="min-h-0 flex-1 overflow-auto">
        {result ? (
          <>
            <p className="px-4 py-2 text-[11px] text-neutral-400">
              {result.results.length} covenants from{" "}
              {result.extraction.text_chars.toLocaleString()} characters ·{" "}
              {result.extraction.model} · {result.extraction.inference_ms}ms
            </p>
            <ul className="divide-y divide-neutral-200 border-y border-neutral-200">
              {result.results.map((item) => (
                <CovenantResult key={`${item.covenant.metric}-${item.covenant.name}`} item={item} />
              ))}
            </ul>
          </>
        ) : (
          <p className="px-4 py-3 text-[12px] text-neutral-400">
            {running
              ? "Extracting covenants, then checking each one…"
              : "Upload a loan agreement to check its covenants against the borrower's data."}
          </p>
        )}
      </div>
    </div>
  );
}
