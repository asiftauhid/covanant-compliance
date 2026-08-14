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

export default function DataPanel() {
  const [tables, setTables] = useState<TableSummary[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [data, setData] = useState<TableData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loading = active !== null && data?.table !== active;
  const activeMeta = tables.find((table) => table.name === active);

  useEffect(() => {
    fetchTables()
      .then((rows) => {
        setTables(rows);
        setActive((current) => current ?? rows[0]?.name ?? null);
      })
      .catch((err: Error) => setError(err.message));
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

        {loading && !error && (
          <p className="px-4 py-6 text-[12px] text-neutral-400">Loading table…</p>
        )}
        {!loading && !error && tables.length === 0 && (
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
