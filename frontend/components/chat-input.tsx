"use client";

// The text box + send button + upload button at the bottom of the chat. It
// only knows how to collect input (typed text, or a chosen file) and hand
// it off — it doesn't talk to the backend itself, that's the chat window's job.
import { useRef, useState, type ChangeEvent, type FormEvent } from "react";

type ChatInputProps = {
  onSend: (text: string) => void;
  onUpload: (file: File) => void;
  disabled: boolean;
};

export function ChatInput({ onSend, onUpload, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue("");
  }

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
    e.target.value = ""; // allow selecting the same file again later
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-2 border-t border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950"
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt"
        onChange={handleFileChange}
        disabled={disabled}
        className="hidden"
      />
      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled}
        aria-label="Upload a document"
        title="Upload a PDF or TXT document"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-zinc-200 text-zinc-500 transition hover:bg-zinc-50 disabled:opacity-40 dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-900"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-4 w-4"
        >
          <path d="M21.44 11.05 12.25 20.24a5.5 5.5 0 0 1-7.78-7.78l9.19-9.19a3.5 3.5 0 0 1 4.95 4.95l-9.19 9.19a1.5 1.5 0 0 1-2.12-2.12l8.49-8.49" />
        </svg>
      </button>

      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask something, or schedule a meeting..."
        disabled={disabled}
        className="flex-1 rounded-full border border-zinc-200 bg-zinc-50 px-4 py-2.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20 disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-900"
      />
      <button
        type="submit"
        disabled={disabled}
        aria-label="Send message"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent text-white transition hover:opacity-90 disabled:opacity-40"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="h-4 w-4 -translate-x-px"
        >
          <path d="M3.4 20.6 22 12 3.4 3.4 3 10l13 2-13 2z" />
        </svg>
      </button>
    </form>
  );
}
