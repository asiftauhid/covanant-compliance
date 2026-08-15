"use client";

import { useEffect, useState } from "react";

import { fetchTableRows, fetchTables } from "@/lib/api";
import type { Cell, TableData, TableSummary } from "@/lib/types";

const ISO_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/;

const TABLE_LABELS: Record<string, string> = {
  borrowers: "Borrowers",
  financial_snapshots: "Financial snapshots",
};

function formatCell(value: Cell) {
  if (value === null) return "—";
  if (typeof value === "number") return value.toLocaleString();
  if (typeof value === "string" && ISO_TIMESTAMP.test(value)) {
    return `${value.slice(0, 10)} ${value.slice(11, 16)}`;
  }
  return String(value);
}

function isNumeric(value: Cell) {
  return (
    typeof value === "number" ||
    (typeof value === "string" && /^-?\d+(\.\d+)?$/.test(value))
  );
}

function tableLabel(name: string) {
  return TABLE_LABELS[name] ?? name.replaceAll("_", " ");
}

function Spinner({ label, hint }: { label: string; hint?: string }) {
  return (
    <div
      className="flex flex-col gap-1.5 px-4 py-8 text-[12px] text-neutral-400"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-2">
        <span
          className="spinner inline-block h-3.5 w-3.5 shrink-0 rounded-full border border-neutral-300 border-t-neutral-800"
          aria-hidden
        />
        {label}
      </div>
      {hint && <p className="pl-[22px] text-[11px] leading-snug text-neutral-400">{hint}</p>}
    </div>
  );
}

export default function DataPanel() {
  const [tables, setTables] = useState<TableSummary[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [data, setData] = useState<TableData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tablesLoading, setTablesLoading] = useState(true);

  const loading = active !== null && data?.table !== active;
  const activeMeta = tables.find((table) => table.name === active);
  const showSpinner = !error && (tablesLoading || loading);

  useEffect(() => {
    fetchTables()
      .then((rows) => {
        setTables(rows);
        setActive((current) => current ?? rows[0]?.name ?? null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setTablesLoading(false));
  }, []);

  useEffect(() => {
    if (!active) return;

    let current = true;
    fetchTableRows(active)
      .then((rows) => {
        if (current) setData(rows);
      })
      .catch((err: Error) => {
        if (current) setError(err.message);
      });

    return () => {
      current = false;
    };
  }, [active]);

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-white">
      <div className="flex shrink-0 items-end justify-between gap-3 border-b border-neutral-200 px-4">
        <div className="flex items-center gap-1 overflow-x-auto">
          {tablesLoading && (
            <span className="flex items-center gap-2 px-3 py-2.5 text-[12px] text-neutral-400">
              <span
                className="spinner inline-block h-3 w-3 shrink-0 rounded-full border border-neutral-300 border-t-neutral-800"
                aria-hidden
              />
              Loading…
            </span>
          )}
          {tables.map((table) => {
            const selected = table.name === active;
            return (
              <button
                key={table.name}
                type="button"
                onClick={() => setActive(table.name)}
                className={`-mb-px border-b-2 px-3 py-2.5 text-[12px] transition-colors ${
                  selected
                    ? "border-neutral-900 text-neutral-900"
                    : "border-transparent text-neutral-500 hover:text-neutral-800"
                }`}
              >
                {tableLabel(table.name)}
                <span className="ml-1.5 tabular-nums text-neutral-400">
                  {table.row_count}
                </span>
              </button>
            );
          })}
        </div>
        {activeMeta && (
          <p className="hidden shrink-0 pb-2.5 text-[11px] text-neutral-400 sm:block">
            {activeMeta.columns.length} columns
          </p>
        )}
      </div>

      {error && (
        <p className="border-b border-red-100 bg-red-50 px-4 py-2 text-[12px] text-red-700">
          {error}
        </p>
      )}

      <div className="min-h-0 flex-1 overflow-auto">
        {data && !loading && (
          <table className="w-full border-collapse text-[12px]">
            <thead className="sticky top-0 z-10 bg-[#fafafa]/90 backdrop-blur-sm">
              <tr className="border-b border-neutral-200 text-left">
                {data.columns.map((column) => (
                  <th
                    key={column}
                    className="whitespace-nowrap px-3 py-2 font-medium text-neutral-500"
                  >
                    {column.replaceAll("_", " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row, index) => (
                <tr
                  key={index}
                  className="border-b border-neutral-100 transition-colors hover:bg-neutral-50"
                >
                  {data.columns.map((column) => (
                    <td
                      key={column}
                      className={`whitespace-nowrap px-3 py-2 ${
                        isNumeric(row[column])
                          ? "text-right tabular-nums text-neutral-800"
                          : "text-neutral-700"
                      }`}
                    >
                      {formatCell(row[column])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {showSpinner && (
          <Spinner
            label={tablesLoading ? "Loading data…" : "Loading table…"}
            hint={
              tablesLoading
                ? "The free deployment on Render can have a cold start, so it might be a bit slower."
                : undefined
            }
          />
        )}
        {!showSpinner && !error && tables.length === 0 && (
          <p className="px-4 py-6 text-[12px] text-neutral-400">
            No readable tables yet.
          </p>
        )}
        {data && !loading && data.rows.length === 0 && (
          <p className="px-4 py-6 text-[12px] text-neutral-400">No rows in this table.</p>
        )}
      </div>
    </div>
  );
}
