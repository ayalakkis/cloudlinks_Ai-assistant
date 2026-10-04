// Shared shape for a single chat bubble: who said it, and what it says.
// Both the chat window and the message bubble use this so they always agree
// on what a "message" looks like.
export type Message = {
  // "system" is used for local status notices (e.g. "file uploaded") --
  // it's never sent to the backend, just displayed differently in the UI.
  role: "user" | "assistant" | "system";
  content: string;
};
