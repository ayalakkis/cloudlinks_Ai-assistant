"use client";

// The main chat screen: header, message list, and input bar. It keeps the
// list of messages in memory, sends each new one to the backend, and shows
// the reply (or a "thinking" animation while waiting).
import { useEffect, useRef, useState } from "react";
import { sendMessage, uploadDocument } from "@/lib/api";
import type { Message } from "@/types";
import { MessageBubble } from "./message-bubble";
import { ChatInput } from "./chat-input";
import { TypingIndicator } from "./typing-indicator";

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  async function handleSend(text: string) {
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setPending(true);

    try {
      const { reply } = await sendMessage(text);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch {
      setError("Couldn't reach the assistant. Is the backend running?");
    } finally {
      setPending(false);
    }
  }

  async function handleUpload(file: File) {
    setError(null);
    setMessages((prev) => [
      ...prev,
      { role: "system", content: `Uploading ${file.name}...` },
    ]);
    setPending(true);

    try {
      const { file_name, chunks_stored } = await uploadDocument(file);
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: `${file_name} uploaded — ${chunks_stored} chunk${chunks_stored === 1 ? "" : "s"} indexed. You can ask about it now.`,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "system", content: err instanceof Error ? err.message : "Upload failed." },
      ]);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex h-full w-full max-w-2xl flex-col overflow-hidden rounded-3xl border border-zinc-200 bg-white shadow-xl shadow-zinc-200/50 dark:border-zinc-800 dark:bg-zinc-950 dark:shadow-black/40">
      <header className="flex items-center gap-3 border-b border-zinc-200 px-5 py-4 dark:border-zinc-800">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-sm font-semibold text-white">
          C
        </div>
        <div>
          <h1 className="text-sm font-semibold">Cloudlinks Assistant</h1>
          <p className="flex items-center gap-1.5 text-xs text-zinc-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Online
          </p>
        </div>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto bg-zinc-50/50 p-5 dark:bg-zinc-950">
        {messages.length === 0 && (
          <p className="text-sm text-zinc-400">
            Ask about stored info, upload a document, or schedule/cancel a meeting.
          </p>
        )}
        {messages.map((message, i) => (
          <MessageBubble key={i} message={message} />
        ))}
        {pending && <TypingIndicator />}
        {error && <p className="text-sm text-red-500">{error}</p>}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={handleSend} onUpload={handleUpload} disabled={pending} />
    </div>
  );
}
