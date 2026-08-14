"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import DataPanel from "@/components/DataPanel";
import RightPanel from "@/components/RightPanel";

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
  const split = useSplitLayout();

  const clamp = (value: number) => Math.min(MAX_PCT, Math.max(MIN_PCT, value));

  const moveTo = useCallback((clientX: number) => {
    const container = containerRef.current;
    if (!container) return;
    const { left, width } = container.getBoundingClientRect();
    setLeftPct(clamp(((clientX - left) / width) * 100));
  }, []);

  return (
    <div className="flex h-dvh flex-col bg-[#f7f7f5] text-neutral-900">
      <header className="shrink-0 border-b border-neutral-200/80 bg-white px-5 py-3">
        <h1 className="text-[14px] font-medium tracking-tight">
          Covenant Compliance
        </h1>
        <p className="mt-0.5 text-[11px] text-neutral-400">
          Browse borrower data on the left; check covenants or chat with data on the
          right
        </p>
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
          className={`group relative hidden w-px shrink-0 bg-neutral-200 md:block ${
            dragging ? "bg-neutral-400" : "hover:bg-neutral-400"
          } focus-visible:bg-neutral-500`}
        >
          <span className="absolute inset-y-0 -left-1.5 -right-1.5 cursor-col-resize" />
          <span
            className={`absolute top-1/2 left-1/2 h-8 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-neutral-300 opacity-0 transition-opacity group-hover:opacity-100 ${
              dragging ? "opacity-100 bg-neutral-400" : ""
            }`}
          />
        </div>

        <section className="flex min-h-0 min-w-0 flex-1 flex-col border-t border-neutral-200 md:border-t-0">
          <RightPanel />
        </section>
      </div>
    </div>
  );
}
