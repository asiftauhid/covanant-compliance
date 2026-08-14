"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import { chatWithData } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

const SUGGESTIONS = [
  "What is ABC Trading LLC's total debt for July 2026?",
  "Which borrowers are in Logistics?",
  "Show cash balance and revenue for Gulf Logistics FZE in July 2026",
];

function cleanMarkup(text: string) {
  return text
    .replace(/\\n/g, "\n")
    .replace(/\\text\{([^}]+)\}/g, "$1")
    .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, "$1 / $2")
    .replace(/\\\(|\\\)|\\\[|\\\]/g, "")
    .replace(/\$\$([\s\S]+?)\$\$/g, "$1")
    .replace(/\$([^$\n]+)\$/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^#{1,6}\s+/gm, "");
}

function renderInline(text: string, keyPrefix: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    const bold = part.match(/^\*\*([^*]+)\*\*$/);
    if (bold) {
      return (
        <strong key={`${keyPrefix}-${index}`} className="font-medium">
          {bold[1]}
        </strong>
      );
    }
    return <span key={`${keyPrefix}-${index}`}>{part}</span>;
  });
}

function ChatText({ text }: { text: string }) {
  const cleaned = cleanMarkup(text).trim();
  const lines = cleaned.split("\n");

  return (
    <div className="space-y-1">
      {lines.map((line, index) => (
        <p key={index} className={line.trim() ? "" : "h-2"}>
          {renderInline(line, String(index))}
        </p>
      ))}
    </div>
  );
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function sendQuestion(question: string) {
    const cleaned = question.trim();
    if (!cleaned || sending) return;

    const nextHistory = [...messages, { role: "user" as const, content: cleaned }];
    setMessages(nextHistory);
    setDraft("");
    setError(null);
    setSending(true);

    try {
      const result = await chatWithData(cleaned, messages);
      setMessages([
        ...nextHistory,
        {
          role: "assistant",
          content: result.answer || "No answer returned.",
        },
      ]);
      if (result.error) setError(result.error);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
      setMessages([
        ...nextHistory,
        {
          role: "assistant",
          content: "Sorry — I could not answer that from the database.",
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    void sendQuestion(draft);
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-[#f7f7f5]">
      <div className="min-h-0 flex-1 overflow-auto px-4 py-4">
        {messages.length === 0 ? (
          <div>
            <p className="text-[13px] text-neutral-700">Ask about the borrower data</p>
            <p className="mt-1 text-[12px] text-neutral-500">
              Questions are answered from the tables on the left — including lookups by
              borrower name.
            </p>
            <ul className="mt-4 space-y-2">
              {SUGGESTIONS.map((suggestion) => (
                <li key={suggestion}>
                  <button
                    type="button"
                    onClick={() => void sendQuestion(suggestion)}
                    className="w-full rounded-sm border border-neutral-200 bg-white px-3 py-2 text-left text-[12px] text-neutral-700 hover:border-neutral-400"
                  >
                    {suggestion}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <ul className="space-y-3">
            {messages.map((message, index) => (
              <li
                key={`${message.role}-${index}`}
                className={`max-w-[92%] rounded-sm px-3 py-2 text-[12px] leading-relaxed ${
                  message.role === "user"
                    ? "ml-auto bg-neutral-900 text-white"
                    : "mr-auto border border-neutral-200 bg-white text-neutral-800"
                }`}
              >
                {message.role === "assistant" ? (
                  <ChatText text={message.content} />
                ) : (
                  message.content
                )}
              </li>
            ))}
            {sending && (
              <li className="mr-auto text-[12px] text-neutral-400">Looking up data…</li>
            )}
            <div ref={bottomRef} />
          </ul>
        )}
      </div>

      {error && (
        <p className="border-t border-red-100 bg-red-50 px-4 py-2 text-[12px] text-red-700">
          {error}
        </p>
      )}

      <form
        onSubmit={handleSubmit}
        className="shrink-0 border-t border-neutral-200 bg-white px-4 py-3"
      >
        <div className="flex gap-2">
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask a question about the data…"
            disabled={sending}
            className="min-w-0 flex-1 rounded-sm border border-neutral-200 px-2.5 py-2 text-[12px] text-neutral-800 disabled:bg-neutral-50"
          />
          <button
            type="submit"
            disabled={sending || !draft.trim()}
            className="rounded-sm bg-neutral-900 px-3 py-2 text-[12px] font-medium text-white hover:bg-neutral-800 disabled:cursor-not-allowed disabled:bg-neutral-300"
          >
            Send
          </button>
        </div>
        {messages.length > 0 && (
          <button
            type="button"
            onClick={() => {
              setMessages([]);
              setError(null);
            }}
            className="mt-2 text-[11px] text-neutral-400 hover:text-neutral-700"
          >
            Clear chat
          </button>
        )}
      </form>
    </div>
  );
}
