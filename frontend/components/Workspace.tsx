"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import CompliancePanel from "@/components/CompliancePanel";
import DataPanel from "@/components/DataPanel";
import { fetchHealth } from "@/lib/api";

const MIN_PCT = 24;
const MAX_PCT = 72;
const DEFAULT_PCT = 46;
const SPLIT_BREAKPOINT = "(min-width: 900px)";

function useSplitLayout() {
  const [enabled, setEnabled] = useState(true);

  useEffect(() => {
    const query = window.matchMedia(SPLIT_BREAKPOINT);
    const sync = () => setEnabled(query.matches);
    sync();
    query.addEventListener("change", sync);
    return () => query.removeEventListener("change", sync);
  }, []);

  return enabled;
}

export default function Workspace() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [leftPct, setLeftPct] = useState(DEFAULT_PCT);
  const [dragging, setDragging] = useState(false);
  const [provider, setProvider] = useState<string | null>(null);
  const split = useSplitLayout();

  useEffect(() => {
    fetchHealth()
      .then((health) => setProvider(`${health.llm_provider} · ${health.model}`))
      .catch(() => setProvider("api offline"));
  }, []);

  const clamp = (value: number) => Math.min(MAX_PCT, Math.max(MIN_PCT, value));

  const moveTo = useCallback((clientX: number) => {
    const container = containerRef.current;
    if (!container) return;
    const { left, width } = container.getBoundingClientRect();
    setLeftPct(clamp(((clientX - left) / width) * 100));
  }, []);

  return (
    <div className="flex h-dvh flex-col bg-neutral-50 text-neutral-900">
      <header className="flex shrink-0 items-baseline gap-3 border-b border-neutral-200 bg-white px-4 py-2.5">
        <h1 className="text-[13px] font-medium">Covenant Compliance Monitor</h1>
        <span className="text-[11px] text-neutral-400">
          {provider ?? "connecting…"}
        </span>
      </header>

      <div
        ref={containerRef}
        className={`flex min-h-0 flex-1 flex-col md:flex-row ${
          dragging ? "cursor-col-resize select-none" : ""
        }`}
      >
        <section
          className="flex min-h-0 min-w-0 flex-1 flex-col md:flex-none"
          style={split ? { width: `${leftPct}%` } : undefined}
        >
          <DataPanel />
        </section>

        <div
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize panels"
          aria-valuenow={Math.round(leftPct)}
          aria-valuemin={MIN_PCT}
          aria-valuemax={MAX_PCT}
          tabIndex={0}
          onPointerDown={(event) => {
            event.currentTarget.setPointerCapture(event.pointerId);
            setDragging(true);
          }}
          onPointerMove={(event) => {
            if (dragging) moveTo(event.clientX);
          }}
          onPointerUp={(event) => {
            event.currentTarget.releasePointerCapture(event.pointerId);
            setDragging(false);
          }}
          onDoubleClick={() => setLeftPct(DEFAULT_PCT)}
          onKeyDown={(event) => {
            if (event.key === "ArrowLeft") setLeftPct((pct) => clamp(pct - 2));
            if (event.key === "ArrowRight") setLeftPct((pct) => clamp(pct + 2));
          }}
          title="Drag to resize · double-click to reset"
          className={`group relative hidden w-px shrink-0 border-0 bg-neutral-200 md:block ${
            dragging ? "bg-neutral-400" : "hover:bg-neutral-400"
          } focus-visible:bg-neutral-500 focus-visible:outline-none`}
        >
          <span className="absolute inset-y-0 -left-1 -right-1 cursor-col-resize" />
        </div>

        <section className="flex min-h-0 min-w-0 flex-1 flex-col border-t border-neutral-200 md:border-t-0">
          <CompliancePanel />
        </section>
      </div>
    </div>
  );
}
