"use client";

import { useEffect, useRef, useState } from "react";

import { analyzeLoanAgreement, fetchBorrowers } from "@/lib/api";
import type {
  Borrower,
  ComplianceStatus,
  CovenantAnalysisItem,
  LoanAnalysisResult,
} from "@/lib/types";

const STATUS_LABEL: Record<ComplianceStatus, string> = {
  compliant: "Compliant",
  warning: "Warning",
  breached: "Breached",
  insufficient_data: "Insufficient data",
  manual_review: "Needs review",
};

const STATUS_TEXT: Record<ComplianceStatus, string> = {
  compliant: "text-emerald-700",
  warning: "text-amber-700",
  breached: "text-red-700",
  insufficient_data: "text-neutral-500",
  manual_review: "text-neutral-500",
};

const STATUS_EDGE: Record<ComplianceStatus, string> = {
  compliant: "border-l-emerald-600",
  warning: "border-l-amber-500",
  breached: "border-l-red-600",
  insufficient_data: "border-l-neutral-300",
  manual_review: "border-l-neutral-300",
};

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  if (Number.isInteger(value)) return value.toLocaleString();
  return Number(value.toPrecision(4)).toString();
}

function summarize(results: CovenantAnalysisItem[]) {
  const counts: Partial<Record<ComplianceStatus, number>> = {};
  for (const item of results) {
    const status = item.check.evaluation.status;
    counts[status] = (counts[status] ?? 0) + 1;
  }
  return counts;
}

function Spinner() {
  return (
    <span
      className="spinner inline-block h-3 w-3 shrink-0 rounded-full border border-neutral-300 border-t-neutral-800"
      aria-hidden
    />
  );
}

function DoneMark() {
  return (
    <span
      className="inline-flex h-3 w-3 shrink-0 items-center justify-center text-[9px] leading-none text-emerald-700"
      aria-hidden
    >
      ✓
    </span>
  );
}

function AnalysisProgress({ period }: { period: string }) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      window.setTimeout(() => setPhase(1), 2200),
      window.setTimeout(() => setPhase(2), 5500),
    ];
    return () => timers.forEach(clearTimeout);
  }, []);

  const steps = [
    "Extracting covenants from the PDF",
    `Pulling figures for ${period}`,
    "Evaluating each covenant",
  ];

  return (
    <div className="px-4 py-8">
      <p className="text-[13px] text-neutral-700">Running check…</p>
      <ol className="mt-4 space-y-3">
        {steps.map((label, index) => {
          const done = index < phase;
          const current = index === phase;
          return (
            <li key={label} className="flex items-center gap-2.5 text-[12px]">
              {done ? <DoneMark /> : current ? <Spinner /> : (
                <span className="inline-block h-3 w-3 shrink-0 rounded-full border border-neutral-200" aria-hidden />
              )}
              <span
                className={
                  current
                    ? "text-neutral-800"
                    : done
                      ? "text-neutral-500"
                      : "text-neutral-400"
                }
              >
                {label}
                {current ? "…" : ""}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function CovenantResult({ item }: { item: CovenantAnalysisItem }) {
  const { evaluation } = item.check;

  return (
    <li
      className={`rounded-sm border border-neutral-200 border-l-[3px] bg-white px-4 py-3.5 ${STATUS_EDGE[evaluation.status]}`}
    >
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-[13px] font-medium text-neutral-900">
          {evaluation.name}
        </h3>
        <span
          className={`shrink-0 text-[11px] font-medium ${STATUS_TEXT[evaluation.status]}`}
        >
          {STATUS_LABEL[evaluation.status]}
        </span>
      </div>

      <p className="mt-1.5 text-[12px] text-neutral-600 tabular-nums">
        Required {evaluation.operator} {formatNumber(evaluation.threshold)}
        <span className="mx-2 text-neutral-300">·</span>
        Actual {formatNumber(evaluation.actual)}
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

      <details className="mt-2 text-[12px]">
        <summary className="cursor-pointer select-none text-neutral-400 transition-colors hover:text-neutral-700">
          <span className="inline-flex items-center gap-1.5">
            <span className="disclosure text-[10px] text-neutral-300">▸</span>
            View how this was calculated
          </span>
        </summary>
        <div className="mt-2.5 space-y-2.5 border-t border-neutral-100 pt-2.5 text-neutral-600">
          <div>
            <p className="mb-1 text-[11px] font-medium text-neutral-400">
              Covenant from PDF
            </p>
            <p className="border-l border-neutral-200 pl-2 text-neutral-600">
              {evaluation.source_text || "—"}
            </p>
          </div>

          <div>
            <p className="mb-1 text-[11px] font-medium text-neutral-400">
              Formula
            </p>
            <pre className="overflow-x-auto whitespace-pre-wrap break-words rounded-sm bg-neutral-50 p-2.5 font-mono text-[11px] leading-relaxed text-neutral-700">
              {evaluation.formula || "—"}
            </pre>
          </div>

          <div>
            <p className="mb-1 text-[11px] font-medium text-neutral-400">
              Data used from DB
            </p>
            {Object.keys(evaluation.inputs).length > 0 ? (
              <dl className="space-y-0.5">
                {Object.entries(evaluation.inputs).map(([name, value]) => (
                  <div key={name} className="flex justify-between gap-4">
                    <dt className="text-neutral-500">{name.replaceAll("_", " ")}</dt>
                    <dd className="tabular-nums text-neutral-800">
                      {value.toLocaleString()}
                    </dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="text-neutral-400">—</p>
            )}
          </div>
        </div>
      </details>
    </li>
  );
}

export default function CompliancePanel() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [borrowers, setBorrowers] = useState<Borrower[]>([]);
  const [borrowerId, setBorrowerId] = useState("");
  const [period, setPeriod] = useState("2026-07");
  const [file, setFile] = useState<File | null>(null);
  const [draggingFile, setDraggingFile] = useState(false);
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

  function acceptFile(next: File | null) {
    if (!next) return;
    if (next.type !== "application/pdf" && !next.name.toLowerCase().endsWith(".pdf")) {
      setError("Please upload a PDF loan agreement.");
      return;
    }
    setError(null);
    setFile(next);
  }

  async function useSample() {
    try {
      const response = await fetch("/loan_agreement_sample.pdf");
      if (!response.ok) throw new Error("Could not load sample PDF");
      const blob = await response.blob();
      acceptFile(new File([blob], "loan_agreement_sample.pdf", { type: "application/pdf" }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load sample PDF");
    }
  }

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

  const counts = result ? summarize(result.results) : null;
  const canRun = Boolean(file && borrowerId && !running);

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-[#f7f7f5]">
      <form
        onSubmit={handleSubmit}
        className="shrink-0 border-b border-neutral-200 bg-white px-4 py-4"
      >
        <div className="max-w-md space-y-3">
          <div>
            <div className="mb-1.5 flex items-baseline justify-between gap-2">
              <label className="text-[12px] font-medium text-neutral-700">
                Loan agreement
              </label>
              <div className="flex items-center gap-2 text-[11px]">
                <a
                  href="/loan_agreement_sample.pdf"
                  target="_blank"
                  rel="noreferrer"
                  className="text-neutral-400 underline-offset-2 hover:text-neutral-700 hover:underline"
                >
                  View sample
                </a>
                <span className="text-neutral-200">·</span>
                <button
                  type="button"
                  onClick={useSample}
                  className="text-neutral-400 underline-offset-2 hover:text-neutral-700 hover:underline"
                >
                  Use sample
                </button>
              </div>
            </div>

            <div
              onDragEnter={(event) => {
                event.preventDefault();
                setDraggingFile(true);
              }}
              onDragOver={(event) => {
                event.preventDefault();
                setDraggingFile(true);
              }}
              onDragLeave={(event) => {
                event.preventDefault();
                if (!event.currentTarget.contains(event.relatedTarget as Node)) {
                  setDraggingFile(false);
                }
              }}
              onDrop={(event) => {
                event.preventDefault();
                setDraggingFile(false);
                acceptFile(event.dataTransfer.files?.[0] ?? null);
              }}
              onClick={() => inputRef.current?.click()}
              className={`cursor-pointer rounded-sm border border-dashed px-3 py-4 transition-colors ${
                draggingFile
                  ? "border-neutral-500 bg-neutral-50"
                  : file
                    ? "border-neutral-300 bg-neutral-50"
                    : "border-neutral-300 hover:border-neutral-400 hover:bg-neutral-50"
              }`}
            >
              <input
                ref={inputRef}
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={(event) => acceptFile(event.target.files?.[0] ?? null)}
              />
              {file ? (
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-[12px] text-neutral-800">{file.name}</p>
                    <p className="mt-0.5 text-[11px] text-neutral-400">
                      {(file.size / 1024).toFixed(1)} KB · PDF
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      setFile(null);
                      if (inputRef.current) inputRef.current.value = "";
                    }}
                    className="shrink-0 text-[11px] text-neutral-400 hover:text-neutral-700"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-[12px] text-neutral-700">
                    Drop a PDF here, or click to browse
                  </p>
                  <p className="mt-1 text-[11px] text-neutral-400">
                    Loan agreement with covenant clauses
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="flex gap-2.5">
            <label className="min-w-0 flex-1 text-[12px] text-neutral-500">
              <span className="font-medium text-neutral-700">Borrower</span>
              <select
                value={borrowerId}
                onChange={(event) => setBorrowerId(event.target.value)}
                className="mt-1 block w-full rounded-sm border border-neutral-200 bg-white px-2.5 py-2 text-[12px] text-neutral-800"
              >
                {borrowers.map((borrower) => (
                  <option key={borrower.id} value={borrower.id}>
                    {borrower.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="w-[8.5rem] text-[12px] text-neutral-500">
              <span className="font-medium text-neutral-700">Period / month</span>
              <input
                value={period}
                onChange={(event) => setPeriod(event.target.value)}
                placeholder="YYYY-MM"
                className="mt-1 block w-full rounded-sm border border-neutral-200 px-2.5 py-2 text-[12px] tabular-nums text-neutral-800"
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={!canRun}
            className="w-full rounded-sm bg-neutral-900 px-3 py-2 text-[12px] font-medium text-white transition-colors hover:bg-neutral-800 disabled:cursor-not-allowed disabled:bg-neutral-300"
          >
            {running ? "Checking covenants…" : "Run compliance check"}
          </button>
        </div>
      </form>

      {error && (
        <p className="border-b border-red-100 bg-red-50 px-4 py-2.5 text-[12px] text-red-700">
          {error}
        </p>
      )}

      <div className="min-h-0 flex-1 overflow-auto">
        {result ? (
          <>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-neutral-200 bg-white px-4 py-2.5">
              <p className="text-[12px] text-neutral-700">
                {result.results.length} covenant
                {result.results.length === 1 ? "" : "s"} checked
              </p>
              <span className="text-neutral-200">|</span>
              <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px]">
                {(
                  [
                    ["compliant", "Compliant"],
                    ["warning", "Warning"],
                    ["breached", "Breached"],
                    ["insufficient_data", "Insufficient data"],
                    ["manual_review", "Needs review"],
                  ] as const
                )
                  .filter(([key]) => counts?.[key])
                  .map(([key, label]) => (
                    <span key={key} className={STATUS_TEXT[key]}>
                      {counts?.[key]} {label.toLowerCase()}
                    </span>
                  ))}
              </div>
            </div>

            <ul className="space-y-2.5 p-3">
              {result.results.map((item) => (
                <CovenantResult
                  key={`${item.covenant.metric}-${item.covenant.name}`}
                  item={item}
                />
              ))}
            </ul>
          </>
        ) : running ? (
          <AnalysisProgress period={period} />
        ) : (
          <div className="px-4 py-8">
            <p className="text-[13px] text-neutral-700">Ready to check</p>
            <ol className="mt-3 space-y-1.5 text-[12px] text-neutral-500">
              <li>1. Upload a loan agreement PDF</li>
              <li>2. Choose the borrower and reporting period / month</li>
              <li>3. Run the check to see each covenant&apos;s status</li>
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}
