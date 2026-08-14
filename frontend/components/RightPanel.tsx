"use client";

import { useState } from "react";

import ChatPanel from "@/components/chatwithdata/ChatPanel";
import CompliancePanel from "@/components/CompliancePanel";

type RightMode = "compliance" | "chat";

export default function RightPanel() {
  const [mode, setMode] = useState<RightMode>("compliance");

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex shrink-0 items-center gap-1 border-b border-neutral-200 bg-white px-3">
        {(
          [
            ["compliance", "Covenant check"],
            ["chat", "Chat with data"],
          ] as const
        ).map(([id, label]) => {
          const active = mode === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => setMode(id)}
              className={`-mb-px border-b-2 px-3 py-2.5 text-[12px] transition-colors ${
                active
                  ? "border-neutral-900 text-neutral-900"
                  : "border-transparent text-neutral-500 hover:text-neutral-800"
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      {mode === "compliance" ? <CompliancePanel /> : <ChatPanel />}
    </div>
  );
}
